# stitches_in_r
 
# Installation

1. clone the repository
2. Open the R project in Rstudio
3. Follow the instructions in `stitches-in-R-setup.Rmd`.  Some of the setup steps must be executed manually, and then once they are, this markdown can be knit to finish the setup. You can read these steps easily either from the markdown or the compiled HTML file that comes with the cloning of the repo.

This only worked for me if I was not on PNNL's VPN.

The pre-knitting steps of this markdown are reproduced here as well: 


# IMPORTANT NOTES

- Necessary to avoid R variable names like `variable.name` since `.` in python is somewhat analogous to `$` in R. 

- There are a bunch of steps you'll have to do before knitting the `STITCHES-dashboard/stitches-in-R-setup.Rmd`.


- only tested on mac

- you might want a couple finder windows open to `usr/local/bin` and your analogous `/Users/snyd535/.virtualenvs/` so that you can check things are getting installed in the right places, and for the virtual environment, further navigate into `/Users/snyd535/.virtualenvs/r-reticulate/bin` and `/Users/snyd535/.virtualenvs/r-reticulate/lib/python3.9/site-packages` - the last one will let you see progress on dependency information because:

- once those steps are followed and this notebook is ready to be knit to install `stitches` from github, do be aware that it has a lot of dependencies that come along for the ride so it takes like 5-10 minutes. In Rstudio, it just kind of looks like it is doing nothing.


- I honestly I don't really understand virtual environments and especially `reticulate` seems sensitive, so if you want to add something to it later,  probably safer to delete the virtual environment and recreate from scratch here with the additions you want.

# BEFORE KNITTING

With what I figured out by trial and error in `figure-out-reticulate-setup.Rmd`, these are the steps needed to set things up so that this markdown's python chunks are executed with the right version of python in the right virtual environment. 

## Step 1 - Python install
 This is outside of Rstudio
- stitches needs python 3.9 (most used to running with 3.9.7 I think)
- downloaded https://www.python.org/downloads/release/python-397/ to make sure it is in `usr/local/bin` on mac (`usr/local/bin/python3.9` exists)


## Step 1b
To avoid an issue when you get to step 6 and try to knit this notebook, go to 

`Applications` and select the dropdown next to `Python 3.9`. Click the `Install.Certificates.command` 

`stitches` needs to be able to access pangeo, which is online, so the whole thing fails without this.

More details including screenshots at the top answer: https://stackoverflow.com/questions/68275857/urllib-error-urlerror-urlopen-error-ssl-certificate-verify-failed-certifica

## Step 2 - `reticulate` install

need `reticulate` to be able to run both python and r code in the same file.

standard `install.packages("reticulate")` 

`Do you want to install from sources the package which needs compilation? (Yes/no/cancel)`

- I had issues with yes and couldn't track down the errors returned
- no worked fine, so went that direction

- because I didn't install the compiled version, I can't execute python blocks in Rstudio like I would an R block without knitting. They only execute when I knit. 

- can test python code in the Rstudio console once everything is set up with `reticulate::repl_python()` (which turns the console into a python console until you use type `quit` to return it to R). This helps with developing code and switching dynamically between R and python blocks. 

- Two catches with this:

1. if you want to execute a for loop in the console via `reticulate::repl_python()`, you have to run JUST the for loop and you'll have to hit enter twice to get it to correctly execute the for loop. If you just include a for loop in a block of commands you paste in and run all at once, it will basically just execute the first iteration of the for loop. This is not a problem when knitting the entire markdown.

2. Because of the nesting of the `STITCHES-dashboard` directory in this R project, the markdown will look for any data directories in `STITCHES-dashboard`. The console will look for any data directories in the same level as the R project. I got around it by a copy of a `data` directory in each place. When I test code from console, it generates data and pulls from the one, and when I knit the markdown, it generates and pulls from the other.
## Step 3 - `r-reticulate` virtual environment

I could not figure out how to force reticulate to use the right version of python and have access to python packages without creating a virtual environment. There are probably some redudancies in the setup.


The below code block must be executed in Rstudio before knitting to set things up to create the virtual environment and make sure pyton 3.9 is included in it:

```{r, eval=FALSE}
###############################################################################
# Force reticulate to use python 3.9 so that python3.9 file gets included when
# we create the virtual environment

Sys.setenv("RETICULATE_PYTHON" = "/usr/local/bin/python3.9")


library(reticulate)

# create a new environment 
virtualenv_create("r-reticulate")

detach("package:reticulate", unload = TRUE)

###############################################################################
# reticulate is weird about being initialized to only a single python so
# that's why we do a lot of `detach` calls.

# Now Force reticulate to look for virtual env. Python 
Sys.setenv("RETICULATE_PYTHON" = "~/.virtualenvs/r-reticulate/bin/python3.9")

library(reticulate)

# # indicate that we want to use a specific virtualenv
# This should force the virtual environment to default to 3.9
use_virtualenv("r-reticulate", required =TRUE)

# check what's loaded now:
print('===========================================')
print('progress 1')
print(py_config())

###############################################################################
```


## Step 4 - close Rstudio and reopen project

This will happen a couple more times at the end of most subsequent steps

## Step 5 - install pkgs to virtual environment

These actually come along for the ride when you install stitches but I tested with more standard packages first to try to figure things out, so I left this in. Model for adding packages to virtual environment in future.

Now I think the virtual environment is setup to default to 3.9 when we load in `reticulate` and tell it to use the virtual environment fresh, without specifying it via `Sys.setenv`:
```{r, eval = FALSE}
library(reticulate)

# # indicate that we want to use a specific virtualenv
# This should force the virtual environment to default to 3.9
use_virtualenv("r-reticulate", required =TRUE)

# check what's loaded now:
print('===========================================')
print('progress 2')
print(py_config())

###############################################################################

# install and import python packages to virtual environment
# numpy
# install 
virtualenv_install("r-reticulate", "numpy")
# import 
numpy <- import("numpy")

# pandas
# install 
virtualenv_install("r-reticulate", "pandas")
# import 
pandas <- import("pandas")


```

You are now setup and can begin using `reticulate` in Rmarkdown and call the packages we just installed. Close Rstudio, reopen, and knit the notebook to execute all of the following:

# Step 6 - Reopen and knit markdown from this point
