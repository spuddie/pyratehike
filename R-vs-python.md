# 2 implementations: R and python

RateHike is implemented as an R package (see
[https://github.com/spuddie/RateHike](https://github.com/spuddie/RateHike)) 
and as a python package (see 
[https://github.com/spuddie/pyratehike](https://github.com/spuddie/pyratehike)).
If you have a preference for either language, that should be the
package of your choice. If you can just as easily use both, you should
probably choose the python package. The goal is to keep them in sync.

pyratehike v1.0.2 and RateHike v1.0.1 are equivalent, with some small
differences elaborated in the last section of this document.

## R package
The R package was created while writing the master's thesis (see the 
[vignette](MastersThesis.md)). 
It is the prototype code. While it is a bit less mature and the unit tests 
are slightly worse as compared to the python code, over future
versions this will evolve. Also, the code between the two versions is
fully benchmarked to give the same results.

## python version
The python version was created afterwards and based on the R version,
as such it is a bit more mature. Also, for python there are more code
checking tools, contributing to the code quality.

## differences
Minor differences exist: the R package has the option to do Hyman
spline interpolation, but while applying this to real data it was
considered to be sub-par, as such it was not included in the python
code. The python code has two options for spline correction: linear or
natural, whereas in R there is only the linear correction. This was
also deemed sub-par while testing on real data, 
as such it will not be included in the R package.
