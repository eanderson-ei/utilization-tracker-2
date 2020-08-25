# README

An app to help EI staff manage towards their utilization target.

Find the app at https://ei-utilization.herokuapp.com.

Data is updated daily around ...

Conda environment: utilization-report-2

##### ToDo:

- [ ] Permanence name from My Utilization to My Projects
- [ ] Add % to My Projects to see time spent relative to MEH
- [ ] Check calculation of Utilization for employee type correction (wrong in stacked area (b/c using adjusted MEH) but right in )
- [ ] Get all emails and staff added to Deltek
- [ ] Add google tracking
- [ ] Add date updated
- [x] Add top-line instructions for My Projects
- [ ] Instructions
  - [ ] Clarity around how utilization is calculated
  - [ ] Clarity around what goes into utilization
- [x] Add prediction function
- [x] Plot prediction
- [x] Populate prediction annotation
- [x] Add Instructions
- [x] Add 'X' for this month's actual utilization/hours
- [x] Add Strategy Year 
- [ ] loop through Strategy Year to calculate average utilization (check for lag)
- [ ] Create username and password list
- [x] Read in name associated with username for initial load
- [x] Add Entries Table
- [ ] Ask JS if we want to weight FTE for employee type (standard or part time)
- [x] Design Projects view
- [ ] Add weekly summary
- [ ] Build team view
- [ ] Add reset graph button (https://plotly.com/python/custom-buttons/ relayout)

##### Deltek Changes to Request

- [ ] Add Column for Standard Time Categories (Billable, R&D, G&A, Time Off, NBD & Marketing). Confirm these with JS first.
- [ ] Rename column header User Defined Code 3 to ...
- [ ] Switch Unbillable time codes to R&D (or appropriate category)
- [ ] Fill in missing data for Org Name or otherwise assign staff to Practice Area
- [ ] Add 'Preferred Name' for employees (e.g., Geeta)
- [x] Add column to allow assigning project to PA and splitting revenue between Practice Areas (Projects have one or  many Practice Areas--managed through additional timecodes)
- [ ] Join Projects and Tasks 
- [ ] Join Orgs and Projects
- [ ] Change 'Projects' to 'Tasks'

**To maintain**:

1. Download Utilization, Projects, and Employees reports from Cognos each Monday AM

2. Activate conda environment `conda activate utilization-report-2`

3. Run compile_hours_working.py.

4. Check CLI for warnings

   1. If a new employee was added, copy `passwords.json` into the Environment Variables Config at heroku for this app
   2. If a project was billed against but is not in the projects table on Deltek, a CSV will be saved out to `data/` showing which entries were missed. Manually add this project to the code (where Chad's project was added)

5. Restart the app (to load changes to the Google Sheet)

   Run `heroku restart` from the root project folder

5. Update [2020 Utilization Tool](https://enviroincentives.sharepoint.com/:x:/g/EbRNKr-tEV9LvtWtuY1IoMMBpsYHU_kI2C1p1jADsxhofA?e=BcvEhC) by copying form `data/hours_report` into 'hours_report' tab
6. Refresh both graphs, , change 'Updated' text

**Requirements**

1. Deltek
   1. New projects are added along with new tasks
   2. New employees are added 
   3. New employees are assigned email addresses

**To deploy changes:**

1. Commit changes to github

   `git commit -am "<message>"`

   `git pull`

   `git push origin master`

2. Push changes heroku:

   `git push heroku master`



#### Tech Problems

- [x] Login system (stretch: registration)
  * Go with everybody has the same password for now. Use login info to personalize initial load.
  * Else you could try to set up a flask authentication system. But that is stretch.
- [ ] Database for storing burn rates and allocations
  * https://www.youtube.com/watch?v=G65iy0AmthM (CRUD Data table)
  * https://www.youtube.com/watch?v=Mf3s0P4aVKw (Part 2, Connect to Database)
- [ ] SQLAlchemy
  - https://towardsdatascience.com/sqlalchemy-python-tutorial-79a577141a91

## Tips & Tricks

#### Workdays remaining

Excel formula to get workdays remaining for DATES (where A2 is first date)

```
=NETWORKDAYS(A2,EOMONTH(A2,0))
```

---

#### Pandas and side effects

A function that operates on a data frame introduces a 'side effect' by operating on a dataframe that is technically outside of the function's scope. While you can return the dataframe after you have made changes, you don't have to. The function takes the reference to the dataframe, makes changes to the 'global' dataframe and those changes are saved. For simplicity, I tend to pass the reference back and forth between function and a return variable so that it's clear that I'm making a change to that object. However, one might expect that the original data frame, referenced by a variable higher up in the script, would still be available, but this is not the case. The old reference now points to the new data frame. To avoid this, create a copy with df.copy(), but be warned that creating lots of dataframe copies may eat up memory.

---

#### Server-Side Caching vs. Database Query

We need to read in a potentially large dataset (all hours entries for all staff). Ideally, we would only load this once. If we create a hidden div to fire the load and save the output to another hidden div, we can then access the data stored in the hidden div without loading it multiple times (which requires authorizing google sheets, an expensive process). The data itself remains on the server and must be sent over the network with each request, however.

However, this could be faster if the data were stored in a connected database and we only query for the individuals we want.

Dash provides a few other options for increasing performance with memoization, for instance, where the data are serialized as JSON and stored client side. (See the Finance Dashboard for example, although note the chart can't be loaded on initial page load, which may be fine for this use case). Return `return df.to_json()`. See [here](https://community.plotly.com/t/sharing-a-dataframe-between-plots/6173).

Another newer option is the cached callback in dash_extensions. This creates a shared store for callbacks client side as well. See [here](https://community.plotly.com/t/show-and-tell-server-side-caching/42854).

# How to Start a Project

1. Create a new directory in `c_dev/`

2. Open GitBash in the new directory

3. Create an environment

   ```bash
   conda create -n <NAME>
   ```

   I recommend calling the environment the same as the project name (i.e., root folder). 

4. Activate the environment

   ```bash
   source activate <NAME>
   ```

   If using the Anaconda Prompt, you'd use `conda activate <NAME>`

5. Initialize git

   ```bash
   git init
   ```

6. Create a .gitignore

   ```bash
   touch .gitignore
   ```

   Populate .gitignore as needed as you go. See [here] for recommended files.

7. Create a `README.md` and open it

   ```bash
   touch README.md
   start README.md
   ```

9. Populate the empty directory with standard folder structure (as you go)

   ```
   |--data
   |   |--raw
   |   |--processed
   |   |--external
   |   |--interim
   |--docs
   |--notebooks
   |--scripts
   |--secrets
   ```

   For example,

   ```bash
   mkdir scripts
   ```

10. Open VS Code in the project folder

    ```bash
    code .
    ```

11. Create new script files using VS Code and start coding

12. Install packages to the environment when needed

    ```bash
    conda install <PACKAGE NAME>
    ```

    See the conda package manager for help with package channels. Note that `pip` and `conda` package managers shouldn't be mixed. Install everything you can with conda, and if a package isn't available on conda, switch to pip and don't use conda again for that project.

13. Create a requirements.txt

    ```bash 
    pip freeze > requirements.txt
    ```

    Note that most of the time you'll want a pip compatible requirements file (e.g., deploying to Heroku). However, if you're collaborating with others using conda, you can create a .yml file instead.

14. Commit with git

15. Create repository on GitHub

16. Push to GitHub



To test as you go, run the script from the command line.
