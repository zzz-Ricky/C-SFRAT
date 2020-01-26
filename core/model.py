from abc import ABC, abstractmethod, abstractproperty

import numpy as np
import sympy as sym
from sympy import symbols, diff, exp, lambdify, DeferredVector, factorial, Symbol, Idx, IndexedBase
import scipy.optimize

import logging

class Model(ABC):
    def __init__(self, *args, **kwargs):
        """
        Initialize Model

        Keyword Args:
            data: Pandas dataframe with all required columns
            metrics: list of selected metric names
        """
        self.data = kwargs["data"]                  # dataframe
        self.metricNames = kwargs["metricNames"]    # selected metric names (strings)
        self.t = self.data.iloc[:, 0].values            # failure times, from first column of dataframe
        self.failures = self.data.iloc[:, 1].values     # number of failures, from second column of dataframe
        self.n = len(self.failures)                     # number of discrete time segments
        self.cumulativeFailures = self.data["Cumulative"].values
        self.totalFailures = self.cumulativeFailures[-1]
        # list of arrays or array of arrays?
        self.covariateData = [self.data[name].values for name in self.metricNames]
        self.numCovariates = len(self.covariateData)
        self.converged = False
        if (self.metricNames == []):
            self.metricString = "None"
        else:
            self.metricString = ", ".join(self.metricNames)

        # logging
        logging.info("Failure times: {0}".format(self.t))
        logging.info("Number of time segments: {0}".format(self.n))
        logging.info("Failures: {0}".format(self.failures))
        logging.info("Cumulative failures: {0}".format(self.cumulativeFailures))
        logging.info("Total failures: {0}".format(self.totalFailures))
        logging.info("Number of covariates: {0}".format(self.numCovariates))

    ################################################
    # Properties/Members all models must implement #
    ################################################
    @property
    @abstractmethod
    def name(self):
        """
        Name of model (string)
        """
        return "Generic Model"

    @property
    @abstractmethod
    def coxParameterEstimateRange(self):
        """
        Define Cox parameter estimate range for root finding initial values
        """
        return [0.0, 0.01]

    @property
    @abstractmethod
    def shapeParameterEstimateRange(self):
        """
        Define shape parameter estimate range for root finding initial values
        """
        return [0.0, 0.1]

    ##################################################
    # Methods that must be implemented by all models #
    ##################################################

    @abstractmethod
    def calcHazard(self):
        pass

    # @abstractmethod
    # def modelFitting(self):
    #     pass

    @abstractmethod
    def runEstimation(self):
        """
        main method that calls others; called by TaskThread
        """
        pass

    def initialEstimates(self):
        #return np.insert(np.random.uniform(min, max, self.numCovariates), 0, np.random.uniform(0.0, 0.1, 1)) #Works for GM and NB2
        # return np.insert(np.random.uniform(0.0, 0.01, self.numCovariates), 0, np.random.uniform(0.998, 0.99999,1))
                                                                    # (low, high, size)
                                                                    # size is numCovariates + 1 to have initial estimate for b
        betasEstimate = np.random.normal(self.coxParameterEstimateRange[0], self.coxParameterEstimateRange[1], self.numCovariates)
        bEstimate = np.random.normal(self.shapeParameterEstimateRange[0], self.shapeParameterEstimateRange[1], 1)
        return np.insert(betasEstimate, 0, bEstimate)


    def LLF_sym(self, hazard):
        # x[0] = b
        # x[1:] = beta1, beta2, ..

        x = DeferredVector('x')
        second = []
        prodlist = []
        for i in range(self.n):
            sum1 = 1
            sum2 = 1
            TempTerm1 = 1
            for j in range(1, self.numCovariates + 1):
                TempTerm1 = TempTerm1 * exp(self.covariateData[j - 1][i] * x[j])
            sum1 = 1 - ((1 - (hazard(i, x[0]))) ** (TempTerm1))
            for k in range(i):
                TempTerm2 = 1
                for j in range(1, self.numCovariates + 1):
                    TempTerm2 = TempTerm2 * exp(self.covariateData[j - 1][k] * x[j])
                sum2 = sum2 * ((1 - (hazard(i, x[0])))**(TempTerm2))
            second.append(sum2)
            prodlist.append(sum1*sum2)

        firstTerm = -sum(self.failures) #Verified
        secondTerm = sum(self.failures)*sym.log(sum(self.failures)/sum(prodlist))
        logTerm = [] #Verified
        for i in range(self.n):
            logTerm.append(self.failures[i]*sym.log(prodlist[i]))
        thirdTerm = sum(logTerm)
        factTerm = [] #Verified
        for i in range(self.n):
            factTerm.append(sym.log(factorial(self.failures[i])))
        fourthTerm = sum(factTerm)

        f = firstTerm + secondTerm + thirdTerm - fourthTerm
        return f, x

    def convertSym(self, x, bh, target):
        return lambdify(x, bh, target)

    def LLF(self, h, betas):
        # can clean this up to use less loops, probably
        second = []
        prodlist = []
        for i in range(self.n):
            sum1 = 1
            sum2 = 1
            TempTerm1 = 1
            for j in range(self.numCovariates):
                TempTerm1 = TempTerm1 * np.exp(self.covariateData[j][i] * betas[j])
            sum1 = 1 - ((1 - h[i]) ** (TempTerm1))
            for k in range(i):
                TempTerm2 = 1
                for j in range(self.numCovariates):
                    TempTerm2 = TempTerm2 * np.exp(self.covariateData[j][k] * betas[j])
                sum2 = sum2*((1 - h[i])**(TempTerm2))
            second.append(sum2)
            prodlist.append(sum1*sum2)

        firstTerm = -sum(self.failures) #Verified
        secondTerm = sum(self.failures)*np.log(sum(self.failures)/sum(prodlist))
        logTerm = [] #Verified
        for i in range(self.n):
            logTerm.append(self.failures[i]*np.log(prodlist[i]))
        thirdTerm = sum(logTerm)
        factTerm = [] #Verified
        for i in range(self.n):
            factTerm.append(np.log(np.math.factorial(self.failures[i])))
        fourthTerm = sum(factTerm)

        return firstTerm + secondTerm + thirdTerm - fourthTerm

    def optimizeSolution(self, fd, B):
        logging.info("Solving for MLEs...")

        try:
            solution = scipy.optimize.broyden1(fd, xin=B)
            logging.info("Using broyden1")
        except scipy.optimize.nonlin.NoConvergence:
            solution = scipy.optimize.fsolve(fd, x0=B)
            logging.info("Using fsolve")
        except:
            logging.info("Could Not Converge")
            solution = [0 for i in range(self.numCovariates + 1)]


        #solution = scipy.optimize.broyden2(fd, xin=B)          #Does not work (Seems to work well until the 3 covariates then crashes)
        #solution = scipy.optimize.anderson(fd, xin=B)          #Works for DW2 - DS1  - EstB{0.998, 0.999} Does not work for DS2
        #solution = scipy.optimize.excitingmixing(fd, xin=B)    #Does not work
        #solution = scipy.optimize.newton_krylov(fd, xin=B)     #Does not work
        #solution = scipy.optimize.linearmixing(fd, xin=B)      #Does not work
        #solution = scipy.optimize.diagbroyden(fd, xin=B)       #Does not Work
        #solution = scipy.optimize.root(fd, x0=B, method='hybr')
        #solution = scipy.optimize.fsolve(fd, x0=B)
        logging.info("MLEs solved.")
        logging.info(solution)
        return solution

    def calcOmega(self, h, betas):
        # can clean this up to use less loops, probably
        prodlist = []
        for i in range(self.n):
            sum1 = 1
            sum2 = 1
            TempTerm1 = 1
            for j in range(self.numCovariates):
                    TempTerm1 = TempTerm1 * np.exp(self.covariateData[j][i] * betas[j])
            sum1 = 1-((1 - h[i]) ** (TempTerm1))
            for k in range(i):
                TempTerm2 = 1
                for j in range(self.numCovariates):
                        TempTerm2 = TempTerm2 * np.exp(self.covariateData[j][k] * betas[j])
                sum2 = sum2*((1 - h[i])**(TempTerm2))
            prodlist.append(sum1*sum2)
        denominator = sum(prodlist)
        numerator = self.totalFailures

        return numerator / denominator

    def calcP(self):
        pass

    def AIC(self, h, betas):
        p = len(betas) + 1 + 1   # number of covariates + number of hazard rate parameters + 1 (omega)
        return 2 * p - np.multiply(2, self.LLF(h, betas))

    def BIC(self, h, betas):
        p = len(betas) + 1 + 1   # number of covariates + number of hazard rate parameters + 1 (omega)
        return p * np.log(self.n) - 2 * self.LLF(h, betas)

    def MVF(self, h, omega, betas, stop):
        # can clean this up to use less loops, probably
        prodlist = []
        for i in range(stop + 1):     # CHANGED THIS FROM self.n + 1 !!!
            sum1 = 1
            sum2 = 1
            TempTerm1 = 1
            for j in range(self.numCovariates):
                TempTerm1 = TempTerm1 * np.exp(self.covariateData[j][i] * betas[j])
            sum1 = 1-((1 - h[i]) ** (TempTerm1))
            for k in range(i):
                TempTerm2 = 1
                for j in range(self.numCovariates):
                    TempTerm2 = TempTerm2 * np.exp(self.covariateData[j][k] * betas[j])
                sum2 = sum2 * ((1 - h[i])**(TempTerm2))
            prodlist.append(sum1 * sum2)
        return omega * sum(prodlist)

    def MVF_all(self, h, omega, betas):
        mvfList = np.array([self.MVF(h, self.omega, betas, dataPoints) for dataPoints in range(self.n)])
        return mvfList

    def MVF_allocation(self, h, omega, betas, stop, x):
        """
        x is vector of covariate metrics chosen for allocation
        """
        # can clean this up to use less loops, probably
        covData = [list(self.covariateData[j]) for j in range(self.numCovariates)]
        
        for j in range(self.numCovariates):
            covData[j].append(x[j]) # append a single variable (x[j]) to the end of each vector of covariate data

        prodlist = []
        for i in range(stop + 1):     # CHANGED THIS FROM self.n + 1 !!!
            sum1 = 1
            sum2 = 1
            TempTerm1 = 1
            for j in range(self.numCovariates):
                TempTerm1 = TempTerm1 * np.exp(covData[j][i] * betas[j])
            sum1 = 1-((1 - h(i, self.b)) ** (TempTerm1))
            for k in range(i):
                TempTerm2 = 1
                for j in range(self.numCovariates):
                    TempTerm2 = TempTerm2 * np.exp(covData[j][k] * betas[j])
                sum2 = sum2 * ((1 - h(i, self.b))**(TempTerm2))
            prodlist.append(sum1 * sum2)
        return -(omega * sum(prodlist)) # must be negative, SHGO uses minimization
    
    def allocationFunction(self, x, *args):
        failures = args[0]
        # i = self.n + failures
        i = self.n
        return self.MVF_allocation(self.hazardFunction, self.omega, self.betas, i, x)
    
    def SSE(self, fitted, actual):
        sub = np.subtract(fitted, actual)
        sseError = np.sum(np.power(sub, 2))
        return sseError

    def intensityFit(self, mvfList):
        difference = [mvfList[i+1]-mvfList[i] for i in range(len(mvfList)-1)]
        return [mvfList[0]] + difference

    def runEstimation(self):
        initial = self.initialEstimates()
        logging.info("Initial estimates: {0}".format(initial))
        f, x = self.LLF_sym(self.hazardFunction)    # pass hazard rate function
        bh = np.array([diff(f, x[i]) for i in range(self.numCovariates + 1)])
        logging.info("Log-likelihood differentiated.")
        logging.info("Converting symbolic equation to numpy...")
        fd = self.convertSym(x, bh, "numpy")
        logging.info("Symbolic equation converted.")
        sol = self.optimizeSolution(fd, initial)
        logging.info("Optimized solution: {0}".format(sol))

        self.b = sol[0]
        self.betas = sol[1:]
        hazard = self.calcHazard(self.b)
        self.modelFitting(hazard, self.betas)

    def modelFitting(self, hazard, betas):
        self.omega = self.calcOmega(hazard, betas)
        logging.info("Calculated omega: {0}".format(self.omega))
        self.llfVal = self.LLF(hazard, betas)      # log likelihood value
        logging.info("Calculated log-likelihood value: {0}".format(self.llfVal))
        self.aicVal = self.AIC(hazard, betas)
        logging.info("Calculated AIC: {0}".format(self.aicVal))
        self.bicVal = self.BIC(hazard, betas)
        logging.info("Calculated BIC: {0}".format(self.bicVal))
        self.mvfList = self.MVF_all(hazard, self.omega, betas)

        # temporary
        if (np.isnan(self.llfVal) or np.isinf(self.llfVal)):
            self.converged = False
        else:
            self.converged = True

        self.sseVal = self.SSE(self.mvfList, self.cumulativeFailures)
        logging.info("Calculated SSE: {0}".format(self.sseVal))
        self.intensityList = self.intensityFit(self.mvfList)

        logging.info("MVF values: {0}".format(self.mvfList))
        logging.info("Intensity values: {0}".format(self.intensityList))

