# PtX-Now

ptx-now is a multi-criteria optimization focusing on the implementation and optimization of power-to-x processes.

The model is implemented using an user interface to allow fast and easy implementation. The optimization can either be the minimization of production costs, the minization of greenhouse gas emissions, or the multi-criteria optimization.

To use the model, following these instructions:

1. Set up the folder structure comprising a folder for the data (place all data here), a folder for the settings (place settings here; settings will be stored here) and results
2. Run main.py
3. Select the set up folders from step 1
4. Choose if you want to work on an existing project/setting (select project then) or a new one, and choose solver
5. After pressing "Ok" you can start setting up your Power-to-X project and optimize it

# To consider

The model optimizes the capacities and operation of the implemented facility to achieve the set objective. There are several options available, allowing a high level of freedom of implementation. However, careful implementation is necessary:

- Limiting the optimization might result in infeasibility. These issues especially show up when components are restricted (flexibility, limited capacities, min/max power etc.). For example, setting fixed capacities for renewable generators might limit electricity generation necessary for production
- Giving too much freedom might result in unbounded problems. These issues especially show up when prices for commodities are implemented. For example, if residual electricity can be sold at a higher price than generation costs, the model will try to build infinite capacities to reduce costs further

# Requirements

Next to the python packages in the dependencies, you need to have a solver installed on your machine. Please be careful that the installed python package can use the solver (check versions)

# Open issues

- Currently, only gurobi solver is fully implemented. Other solvers have been implemented but not maintained fully
- Visualization of results has not been maintained and has been deactivated
