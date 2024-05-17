# -*- coding: utf-8 -*-
"""
Add Periods and Remove Spaces.ipynb

"""

def add_periods(paragraph):
    result = []
    for i in range(len(paragraph)):
        # Check if the current character is a capital letter and not the first character
        if paragraph[i].isupper() and i > 0:
            result.append(". ")
        # Append the current character to the result list
        result.append(paragraph[i])
    new_paragraph = ''.join(result)
    return new_paragraph

def remove_extra_spaces(text):
    words = text.split()
    new_text = ' '.join(words)
    return new_text

def push_punctuations(text):
    punctuations = [".", ",", ";", ":", "/", "?", "!", "\\"]
    counter = 0
    for i in range(len(text)):
        if text[i - counter] in punctuations and text[i - 1 - counter] == " ":
          text = text[:i - 1 - counter] + text[i - counter:]
          counter += 1
        elif text[i - counter] == " " and text[i - 1 - counter] == "/":
          text = text[:i - counter] + text[i - counter + 1:]
          counter += 1
    return text

def remove_double_periods(input_string):
    result_string = input_string.replace("..", ".")
    return result_string

df = pd.read_excel('C:/Users/Bailey Ng/Desktop/nov_2022.xlsx', sheet_name='Sheet2')

# column number of PHAC Narrative
column_index = 18
column = df.iloc[:, column_index]

for i, cell in enumerate(column):
    column[i] = (remove_double_periods(push_punctuations(add_periods(remove_extra_spaces(str(cell))))))

df.to_excel('C:/Users/Bailey Ng/Desktop/nov_2022.xlsx', sheet_name='Sheet2', index=False)