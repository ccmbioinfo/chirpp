
# CHIRPP Section remover

This repository contains prorgams aimed at removing sections and information not related or pertaining to CHIRPP specific use cases.

## Testing

To test this repository, the following code can be used.
```
from make_narrative import make_nars
import pandas as pd

# Use use the second sheet from the excel file "jan_2023.xlsx"
df = pd.read_excel("jan_2023.xlsx", sheet_name=1)

# Apply the narratives to a new dataframe and save the output to an excel file
df['testNars'] = df['SK Narrative'].apply(make_nars)
df.to_excel('output1.xlsx', engine='xlsxwriter')  
```
