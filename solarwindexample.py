#%%
import generation
import matplotlib.pyplot as plt
import numpy as np

solargenerator=generation.SolarModel(sites=[2], year_min=2010, year_max=2012, data_path='W:/SCORES-DATA/adjustedsolar/')

print(solargenerator.get_load_factor())
#%%
solarpowerout=solargenerator.power_out_array

print(f"Solar length:{len(solarpowerout)}")
plt.plot(solarpowerout)

# %%
