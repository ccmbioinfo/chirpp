type Dictionary = { [key: string]: string };

const dictionary: Dictionary = {
  'hx': 'history',
  '#': 'fracture',
  'fx': 'fracture',
  'c/o': 'complaining of',
  'f/u': 'follow up',
  'fu': 'follow up',
  'w': 'with',
  'ortho': 'orthopaedics',
  'psych': 'psychiatry',
  'cardio': 'cardiology',
  'ophtho': 'ophthalmology',
  'optho': 'opthalmology',
  'ENT': 'otolaryngology',
  'plastics': 'plastic surgery',
  'physio': 'physiotherapy',
  'heme': 'hematology',
  'rx': 'prescription',
  'tx': 'treatment',
  'd': 'days ago',
  'mo': 'months',
  'lac': 'laceration',
  '@': 'at',
  'hpi': 'history of',
  'abx': 'antibiotics',
  'rom': 'range of motion',
  'prox': 'proximal',
  'wb': 'weight bear',
  'dist': 'distal',
  'min': 'minutes',
  'mins': 'minutes',
  'sec': 'seconds',
  'secs': 'seconds',
  'hr': 'hours',
  'hrs': 'hours',
  'fb': 'foreign body',
  'hi': 'head injury',
  'approx': 'approximately',
  'sw': 'social worker',
  'sx': 'symptoms',
  'sh': 'self-harm',
  'pt': 'patient',
  "pt's": "patient's",
  'r': 'right',
  'rt': 'right',
  'l': 'left',
  'lt': 'left',
  'bsa': 'Body Surface Area',
  'tbsa': 'Total Body Surface Area',
  'ed': 'emergency department',
  'pip': 'proximal interphalangeal joint',
  'mt': 'metatarsal',
  'hep b': 'Hepatitis B',
  'loonie': '$1 coin',
  'toonie': '$2 coin',
  'OCD': 'Obsessive-Compulsive Disorder',
  'ADHD': 'Attention Deficit Hyperactivity Disorder',
  'BPD': 'Borderline Personality Disorder',
  'PTSD': 'Post-Traumatic Stress Disorder',
  'MDD': 'Major Depressive Disorder',
  'GDD': 'Global Developmental Delay',
  'ASD': 'Autism Spectrum Disorder',
  'GAD': 'Generalized Anxiety Disorder',
  'ODD': 'Oppositional Defiant Disorder',
  'LD': 'learning disability',
  'DMDD': 'Disruptive Mood Dysregulation Disorder',
  'NAFLD': 'Non-alcoholic Fatty Liver Disease',
  'foosh': 'fall on an outstretched hand',
  'TMJ': 'Temporomandibular Joint',
  'MCP': 'metacarpophalangeal',
  'OD': 'overdose',
  'GnRH': 'Gonadotropin-Releasing Hormone',
  'trans': 'transgender',
  'WIC': 'walk-in clinic',
  'si': 'suicidal ideations',
  'LOC': 'loss of consciousness',
  'CT': 'Computed Tomography',
  'TTC': 'Toronto Transit Commission',
  'FMD': 'family medical doctor',
  'PCP': 'primary care provider',
  'PMD': 'doctor of primary medicine',
  'MVC': 'motor vehicle collision',
  'EMS': 'Emergency Medical Services',
  'EKG': 'electrocardiogram',
  'ECG': 'electrocardiogram',
  'NBNB': 'non-bloody, non-bilious',
  'dw': 'discussed with',
  'RUQ': 'right upper quadrant',
  'abdo': 'abdomen',
  'CVH': 'Credit Valley Hospital',
  'RVH': 'Royal Victoria Hospital',
  'NYGH': 'North York General Hospital',
  'MSH': 'Markham Stouffville Hospital',
  'd/t': 'due to',
  'h/o': 'history of',
  'ER': 'emergency room',
  'XR': 'x-ray',
  'MD': 'medical doctor'
};

const lowercaseDict: Dictionary = Object.fromEntries(Object.entries(dictionary).map(([key, value]) => [key.toLowerCase(), value]));
const sortedDict: Dictionary = Object.keys(lowercaseDict).sort().reduce((acc, key) => {
  acc[key] = lowercaseDict[key];
  return acc;
}, {} as Dictionary);
const reversedDict: Dictionary = Object.keys(sortedDict).reverse().reduce((acc, key) => {
  acc[key] = sortedDict[key];
  return acc;
}, {} as Dictionary);

const termsToReplace: string[] = Object.keys(reversedDict);
const replacements: string[] = Object.values(reversedDict);

const termMapping: Dictionary = Object.fromEntries(termsToReplace.map((key, index) => [key.toLowerCase(), replacements[index]]));

const patterns: string[] = termsToReplace.map(term => `(?<![a-zA-Z0-9])${term}(?![a-zA-Z0-9])`);
const pattern: RegExp = new RegExp(patterns.join('|'), 'gi');

const removeExtraSpaces = (text: string): string => {
  const words = text.split(/\s+/);
  return words.join(' ');
};

const capitalizeSentences = (text: string): string => {
  const sentences = text.split('. ');
  return sentences.map(sentence => sentence.charAt(0).toUpperCase() + sentence.slice(1)).join('. ');
};

const pushPunctuations = (text: string): string => {
  const punctuations = [".", ",", ";", ":", "/", "?", "!", "\\"];
  let counter = 0;
  for (let i = 0; i < text.length; i++) {
    if (punctuations.includes(text[i - counter]) && text[i - 1 - counter] === " ") {
      text = text.slice(0, i - 1 - counter) + text.slice(i - counter);
      counter++;
    } else if (text[i - counter] === " " && text[i - 1 - counter] === "/") {
      text = text.slice(0, i - counter) + text.slice(i - counter + 1);
      counter++;
    }
  }
  return text;
};

const replaceTerms = (match: string): string => {
  const term = match.toLowerCase();
  const replacement = termMapping[term];
  return replacement || match;
};

const modifyText = (text: string): string => {
  const modifiedText = text.replace(new RegExp(`(?<=\\d)(?=${termsToReplace.join('|')})`, 'gi'), ' ');
  return modifiedText.replace(pattern, replaceTerms);
};

const final = (text: string): string => {
  let newText = capitalizeSentences(removeExtraSpaces(text));
  if (!newText.endsWith('.')) {
    newText += '.';
  }
  return newText;
};


const summaryCleanup = (text: string): string => {
  if (!text) {
    return '';
  } else {
    text = text.trim();
    const newText = capitalizeSentences(removeExtraSpaces(text));
    const pushedText = pushPunctuations(newText);
    const replacedText = modifyText(pushedText);
    return final(replacedText);
  }
};


function processColumn(sheet: ExcelScript.Worksheet, columnIndex: number): void {
  const range = sheet.getUsedRange();
  const rowCount = range.getRowCount();

  for (let i = 1; i < rowCount; i++) {
    const cell = range.getCell(i, columnIndex);
    const cellValue = cell.getValue() as string;

    if (cellValue) {
      const cleanedText = summaryCleanup(cellValue);
      cell.setValue(cleanedText);
    }
  }
}

function main(workbook: ExcelScript.Workbook) {
  const sheet = workbook.getActiveWorksheet();
  const columnIndex = 19; // Replace with the index of the column you want to process
  processColumn(sheet, columnIndex);
}