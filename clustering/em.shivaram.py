#!/usr/bin/env python

import math

CONVERGENCE_THRESHOLD = 1e-4

NUM_STATES = 4

FILE = "hmm-gauss.dat"
TEST_FILE = "hmm-test.dat"

def read_input(f):
    data = []
    with open(f) as datafile:
        for line in datafile.readlines():
            points = line.split()
            data.append([float(pt) for pt in points])
    return data      

def calculate_isotropic_bivariate_normal_pdf(x, mu, sigma):
    exp1 = -1.*(x[0] - mu[0])*(x[0] - mu[0]) / (2.*sigma[0])
    exp2 = -1.*(x[1] - mu[1])*(x[1] - mu[1]) / (2.*sigma[1])
    dr1 = math.sqrt(2.*math.pi * sigma[0])
    dr2 = math.sqrt(2.*math.pi * sigma[1])
    return math.exp(exp1) * math.exp(exp2) * (1. / dr1) * (1. / dr2)

def get_obs_likelihood(obs, mu, sigma):
    pdfs = []
    for i in range(NUM_STATES):
        pdfs.append(calculate_isotropic_bivariate_normal_pdf(obs, mu[i], sigma[i]))
    return pdfs

def normalize(vec):
    sum = float(sum(vec))
    if (sum == 0.):
        sum = 1.0
    return map(lambda x: x/sum, vec)

def emstep(data, prior, mu, sigma, loglikOnly):

    num_samples = len(data)
    loglik = 0.
  
    # E-step
    # First compute the activations for each sample point
    activations = []
    for x in range(num_samples):
        a = []
        for s in range(NUM_STATES):
            a.append((0.,0.))
        activations.append(a)
    for x in range(num_samples):
        activations[x] = get_obs_likelihood(data[x], mu, sigma)

    # Compute the log-likelihood by multiplying activations with the prior
    for d in range(num_samples):
        prob_s = 0.
        for s in range(NUM_STATES):
            prob_s = prob_s + (activations[d][s] * prior[s])
        loglik = loglik + math.log(prob_s)

    if (loglikOnly):
        return loglik

    # Now calculate the posterior distribution for each sample point
    post = []
    for x in range(num_samples):
        post.append([0.]*NUM_STATES)
    for d in range(num_samples):
        for s in range(NUM_STATES):
            post[d][s] = prior[s] * activations[d][s]
        if d < 10:
            print "unnorm", post[d]
    
    #print "Posterior:\n", post[0]
    # Normalize posterior for each sample
    # This will make the posterior for each sample to add up to 1.
    for d in range(num_samples):
        sample_sum = float(sum(post[d]))
        if d < 10:
            print "sample_sum", sample_sum
        if sample_sum != 0:
            for s in range(NUM_STATES):
                post[d][s] = post[d][s] / sample_sum
        if d < 10:
            print post[d]

    #print "Posterior:\n", post[0]
    # M-step
    # Update the prior by using the posterior
    for s in range(NUM_STATES):
        sample_sum = 0.
        for x in range(num_samples):
            sample_sum += post[x][s]
        prior[s] = sample_sum / num_samples
        
    # Update mu = post(x) * obs / sum_t(post(x))
    for s in range(NUM_STATES):
        prob1 = 0.
        prob2 = 0.
        for d in range(num_samples):
            prob1 = prob1 + (post[d][s] * data[d][0])
            prob2 = prob2 + (post[d][s] * data[d][1])
        dr = float(prior[s]*num_samples)
        mu[s] = (prob1/dr, prob2/dr)

    # Update sigma = post(x) * (obs - mu) (obs - mu)' / sum_t(post(x))
    for s in range(NUM_STATES):
        nr = 0.
        for x in range(num_samples):
            omu = (data[x][0] - mu[s][0], data[x][1] - mu[s][1])
            omu_omut = (omu[0]*omu[0]) + (omu[1]*omu[1])
            nr += float(post[x][s]*omu_omut)
        dr = prior[s]*2.*num_samples 
        sigma[s] = (nr / dr, nr / dr)

    return loglik

def learn_gmm(file, iter, test_file):
    data = read_input(file)
   
    prior = map(lambda x: x/NUM_STATES, [1.]*NUM_STATES)

    mu = [(0.,0.)]*NUM_STATES

    mu[0] = (0.15, 0.231)
    mu[1] = (-0.121, 0.435)
    mu[2] = (-0.489, -0.890)
    mu[3] = (0.98, -0.678)

    sigma = [(1., 1.)]*NUM_STATES 
    current_ll = 0.
    
    for it in range(iter):
        prev_log_lik = current_ll
        current_ll = emstep(data, prior, mu, sigma, False)
        print "new log_lik", current_ll
        for s in range(NUM_STATES):
            print mu[s]
        print "Priors:"
        for s in range(NUM_STATES):
            print prior[s]
        if (abs(current_ll - prev_log_lik) < CONVERGENCE_THRESHOLD):
            print "converged to", current_ll, "in", it, "iterations"
            break

    print "Means of component densities:\n", mu
    print "Priors:\n", prior
    print "Sigmas:\n", sigma

learn_gmm(FILE, 100, TEST_FILE)
