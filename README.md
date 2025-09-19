# CHIRPP Project Documentation

## Project Overview

The CHIRPP (Clinical Health Informatics Record Processing Platform) project is designed to process and analyze medical notes. Its primary goals are to perform inference for tasks like classification (e.g., identifying patient conditions) and summarization (e.g., creating concise summaries of lengthy medical records). The platform also aims to generate comprehensive reports based on these analyses.

CHIRPP achieves this through a modular architecture involving several key stages:
*   **Data Preprocessing (`Preprocess`)**: This stage focuses on cleaning and preparing the raw medical notes for analysis. This may include tasks like text normalization, removing irrelevant information, and structuring the data.
*   **Inference (`Inference`)**: This core component utilizes machine learning models or other analytical techniques to perform classification and summarization on the preprocessed medical notes.
*   **Data Management (`DataBase`)**: This component likely handles the storage and retrieval of medical notes, processed data, and generated results.
*   **Postprocessing and Reporting (`PostProcess`)**: After inference, this stage involves formatting the results, potentially combining information from different analyses, and generating user-friendly reports.

This document outlines the project's objectives and key components in more detail.

## Project Objectives

The main objectives of the CHIRPP project are:

* Classify chirpp cases from all the ED presentations
* Generate reports for human review
* Create a one-stup shop for full text search

## Key Components

The CHIRPP project consists of the following key components:

* Note reading and pre processing
* Inference using a selection of custom fine-tuned models to extract information
* Postprocessing to generate human readable reports
* Pushing results to a database with LLM embeddings and postgres ts vector indexing

## Classes

This section provides details about the core classes within the CHIRPP project.

### `chirpp.database.database.DataBase`

The `DataBase` class is responsible for managing all interactions with the project's database. Its key roles include:

*   **Adding and Updating Notes**: Facilitating the storage and modification of medical notes within the database.
*   **Processing Data Dumps**: Handling the ingestion and processing of bulk data dumps, likely for initial data population or updates.
*   **Generating Reports**: Extracting and formatting data to create reports based on the information stored in the database.

Key methods of the `DataBase` class include:

*   `process_dump()`: Processes a data dump to populate or update the database.
*   `process_report()`: Generates reports from the database.
*   `import_processed_notes()`: Imports notes that have already undergone some form of processing.
*   `get_raw()`: Retrieves raw data or notes from the database.
*   `get_report()`: Retrieves generated reports or data required for report generation.

### `chirpp.inference.inference.Inference`

The `Inference` class is central to the CHIRPP project's analytical capabilities. It is responsible for loading and utilizing machine learning models to perform various inference tasks on medical notes. Its primary functions include:

*   **Classification**: Categorizing notes or extracting specific information (e.g., intent, substance, I/O, AM/PM, location, area).
*   **Summarization**: Generating concise summaries of longer medical texts.
*   **Embedding Generation**: Creating numerical representations (embeddings) of text data, which can be used for various downstream tasks like similarity analysis or as input to other models.

Key methods of the `Inference` class include:

*   `classify()`: Performs a general classification task.
*   `summarize()`: Generates a summary of the input text.
*   `get_intent()`: Specifically classifies the intent of the note.
*   `get_substance()`: Identifies substances mentioned in the note.
*   `get_io()`: Determines input/output status.
*   `get_ampm()`: Identifies AM/PM time references.
*   `get_location()`: Extracts location information.
*   `get_area()`: Determines the area associated with the note.
*   `get_embeddings()`: Generates embeddings for the input text.

The class also defines a custom exception:

*   `chirpp.inference.inference.NoModelError`: This exception is raised if a model required for an inference task has not been loaded or provided, preventing the system from proceeding with operations that depend on that model.

### `chirpp.postprocess.postprocess.PostProcess`

The `PostProcess` class handles the transformation of raw and inference-enriched notes into structured formats suitable for reporting and analysis. Its main responsibilities include:

*   **Creating Report Templates**: Generating templates or structures for final reports.
*   **Autofilling Columns**: Populating predefined fields or columns in reports or processed data structures based on the information extracted from notes and inference results.

Key methods of the `PostProcess` class include:

*   `autofill()`: Automatically fills in data fields based on processed note information.
*   `create_report()`: Generates a structured report from the processed data.

### `chirpp.preprocess.preprocess.SectionRemover`

The `SectionRemover` class is a utility used during the preprocessing stage. Its specific role is to identify and remove predefined, unnecessary sections from medical notes. This helps in cleaning the input data and focusing subsequent analyses on the most relevant parts of the text.

Key methods of the `SectionRemover` class include:

*   `remove_sections()`: Takes a note as input and returns a version of the note with specified sections removed.

### `chirpp.preprocess.preprocess.Preprocess`

The `Preprocess` class orchestrates the initial cleaning and preparation of raw medical notes before they are fed into the inference models or stored in the database. Its main responsibilities are:

*   **Filtering Notes**: Selecting notes that meet certain criteria or relevance thresholds.
*   **Merging Notes**: Combining related notes or note fragments into a cohesive whole.
*   **Cleaning Notes**: Performing various cleaning operations, potentially including the use of `SectionRemover`, to ensure data quality.

Key methods of the `Preprocess` class include:

*   `read_raw_notes()`: Reads or loads raw medical notes from a source.
*   `get_relevant_notes()`: Filters the notes to retrieve only those considered relevant for further processing.
*   `merge_notes()`: Merges multiple notes into a single, consolidated note.

## Database Schema

This section outlines the structure of the database used by the CHIRPP project. The schema is defined using SQLAlchemy and includes tables for storing patient information, visit details, medical notes, processed data, and user management.

### `Patients`

*   **Table Name**: `patients`
*   **Description**: Stores basic information about patients.
*   **Key Columns**:
    *   `mrn`: Medical Record Number (Primary Key).
    *   `dob`: Date of Birth.

### `Visits`

*   **Table Name**: `visits`
*   **Description**: Contains detailed information about each patient visit.
*   **Key Columns**:
    *   `csn`: Contact Serial Number (Primary Key), uniquely identifies a visit.
    *   `mrn`: Foreign Key to `patients.mrn`.
    *   `sex`: Patient's sex.
    *   `age`: Patient's age at the time of visit.
    *   `arrival_date`, `arrival_time`: Date and time of arrival.
    *   `postal_code`: Patient's postal code.
    *   `chief_complaint`: Main reason for the visit.
    *   `diagnosis`: Diagnosed condition.
    *   `disposition`: Outcome of the visit (e.g., admitted, discharged).
    *   `ctas`: Canadian Triage and Acuity Scale score.
    *   `los`: Length of Stay.
    *   `processed`: Boolean indicating if the visit record has undergone human review/processing.
    *   `address`, `city`, `province`: Patient's address details.

### `Referrals`

*   **Table Name**: `referrals`
*   **Description**: Stores information about referrals made during a visit.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `csn`: Foreign Key to `visits.csn`.
    *   `referrals`: Details of the referral.

### `Problems`

*   **Table Name**: `problems`
*   **Description**: Lists specific problems or conditions identified during a visit.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `csn`: Foreign Key to `visits.csn`.
    *   `problem`: Description of the problem.

### `Notes`

*   **Table Name**: `notes`
*   **Description**: Stores raw medical notes associated with a visit. This table includes a text search vector for efficient searching.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `csn`: Foreign Key to `visits.csn`.
    *   `note_type`: Type of note (e.g., physician note, nursing note).
    *   `author_type`: Type of author (e.g., MD, RN).
    *   `author_service`: Service or department of the author.
    *   `note_text`: The raw text content of the note.
    *   `notes_ts_vector`: A precomputed tsvector for full-text search on `note_text`.

### `ProcessedNotes`

*   **Table Name**: `processed_notes`
*   **Description**: Stores notes that have undergone preprocessing and embedding generation. This table is likely used to cache results from computationally intensive operations.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `csn`: Foreign Key to `visits.csn`.
    *   `note_text`: The processed text of the note.
    *   `note_text_ts_vector`: A tsvector for full-text search on the processed note text.
    *   `jina_query_embed`, `jina_pass_embed`, `jina_sep_embed`, `jina_class_embed`, `jina_match_embed`: Vector embeddings generated by JINA models for different purposes.

### `Cases` (aliased as `chirpp_report`)

*   **Table Name**: `chirpp_report`
*   **Description**: This table appears to store consolidated information for reporting purposes, likely for specific cases of interest (e.g., injury surveillance). It includes many detailed fields related to injury incidents and patient disposition, as well as text search vectors for narratives.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `csn`: Foreign Key to `visits.csn`.
    *   Numerous fields for injury details (date, time, location, type, narratives like `sk_narratvie`, `phac_narrative`), patient information, disposition, and substance involvement.
    *   Text search vectors (`phac_ts_vector`, `notes_ts_vector`, `sk_ts_vector`) for different narrative fields.

### `CustomLabels`

*   **Table Name**: `custom_labels`
*   **Description**: Stores definitions for custom labels that can be applied to visits for research or specific tracking purposes. Supports context-aware searching based on JSON rules.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `label_name`: Name of the custom label.
    *   `label_description`: Description of the label.
    *   `key_words`: Keywords associated with the label.
    *   `context_aware`: Boolean indicating if context-aware rules apply.
    *   `context_rules`: JSON field for storing context-aware search rules.
    *   `active`: Boolean indicating if the label is currently active.

### `CustomLabelVisits`

*   **Table Name**: `custom_label_visits`
*   **Description**: A linking table that associates `CustomLabels` with specific `Visits`.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `label_id`: Foreign Key to `custom_labels.id`.
    *   `csn`: Foreign Key to `visits.csn`.

### `Users`

*   **Table Name**: `users`
*   **Description**: Stores information about users of the CHIRPP system.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `first_name`, `last_name`: User's name.
    *   `email`: User's email address.
    *   `password`: Hashed password for the user.
    *   `active`: Boolean indicating if the user account is active.

### `Managers`

*   **Table Name**: `managers`
*   **Description**: Defines a hierarchical relationship between users, indicating who manages whom.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `user_id`: Foreign Key to `users.id` (the manager).
    *   `manages`: Foreign Key to `users.id` (the user being managed).

### `Logs`

*   **Table Name**: `logs`
*   **Description**: Keeps a record of activities performed within the CHIRPP system for auditing and tracking purposes.
*   **Key Columns**:
    *   `id`: Auto-incrementing primary key.
    *   `user`: Foreign Key to `users.id`, indicating who performed the action.
    *   `timestamp`: Date and time of the logged activity.
    *   `command`: Description of the command or action performed.

## Preprocessing Steps

The preprocessing of raw medical notes is a critical initial phase in the CHIRPP workflow, ensuring that the data fed into the inference models is clean, relevant, and structured. This process primarily involves the `Preprocess` class, which may utilize the `SectionRemover` class for specific cleaning tasks.

The typical preprocessing pipeline is as follows:

1.  **Reading Raw Notes**: The `Preprocess.read_raw_notes()` method is used to ingest raw medical notes from their source. These notes are often unstructured and may contain a mix of relevant and irrelevant information.

2.  **Filtering Relevant Notes**: Once loaded, the notes undergo a filtering stage using `Preprocess.get_relevant_notes()`. This step aims to sift through the raw data and select only those notes that are pertinent to the project's objectives (e.g., specific types of notes, notes from particular departments, or notes containing certain keywords).

3.  **Removing Unwanted Sections**: A key part of cleaning the notes involves removing sections that are not useful for analysis or may introduce noise. The `SectionRemover.remove_sections()` method is employed for this purpose. It typically operates based on a predefined set of rules or patterns that identify headers or segments of text to be excised (e.g., administrative information, standard disclaimers, or sections deemed irrelevant to clinical analysis). The `Preprocess` class would call upon `SectionRemover` during its cleaning routines.

4.  **Merging Notes**: For a single patient visit, there might be multiple notes created by different healthcare providers or at different times. The `Preprocess.merge_notes()` method is used to consolidate these disparate notes into a single, coherent document for that visit. This ensures that all relevant information for an encounter is available in one place for subsequent processing.

5.  **Further Cleaning (Implied)**: Beyond section removal, the `Preprocess` class may perform other cleaning operations such as correcting common typographical errors, normalizing abbreviations, or standardizing date/time formats, although specific methods for these are not explicitly listed but are common preprocessing tasks.

The output of these preprocessing steps is a set of cleaned and structured notes, ready for the `Inference` stage where machine learning models will extract insights, or for storage in the `ProcessedNotes` table.

## Inference Process

Once medical notes have been preprocessed, the `Inference` class takes center stage. This class is the hub for all machine learning model-based predictions within the CHIRPP project. It loads and utilizes various models to extract meaningful information and insights from the cleaned note data.

Key functionalities of the `Inference` class include:

1.  **Note Classification**:
    *   Models are used to classify notes based on predefined categories. For example, a primary use case is determining if a note or a collection of notes for a visit constitutes a "CHIRPP case" (e.g., an injury case relevant to the Canadian Hospitals Injury Reporting and Prevention Program). This often involves binary or multi-class classification models invoked via the generic `classify()` method or more specialized internal methods.

2.  **Content Summarization**:
    *   For lengthy medical notes, the `summarize()` method employs summarization models to generate concise versions, capturing the most critical information. This is particularly useful for quick reviews and report generation.

3.  **Specific Information Extraction**:
    *   The `Inference` class uses targeted models to extract various discrete pieces of information from the notes. This can include:
        *   `get_intent()`: Determining the likely intent behind an injury or event (e.g., accidental, intentional).
        *   `get_substance()`: Identifying mentions of substance use (e.g., alcohol, drugs).
        *   `get_location()`: Extracting the location where an incident or injury occurred.
        *   `get_area()`: Pinpointing the specific area of the body affected.
        *   Other methods like `get_io()` (input/output) and `get_ampm()` (time of day) also fall under this category of specific data point extraction.

4.  **Text Embedding Generation**:
    *   Using the `get_embeddings()` method, the `Inference` class can convert text from notes into dense vector representations (embeddings). These embeddings are highly valuable for:
        *   Similarity searches (e.g., finding similar notes or cases).
        *   Input features for other machine learning models.
        *   Clustering and data visualization.
    The `ProcessedNotes` table stores some of these generated embeddings (e.g., `jina_query_embed`, `jina_pass_embed`).

It's important to note that the `Inference` class relies on having the appropriate models loaded. If a required model is missing, it raises a `NoModelError` to prevent errors in downstream processing. The results from these inference tasks are then typically passed to the `PostProcess` stage for report generation and data structuring.

## Postprocessing Steps

After the raw notes have been enriched with insights by the `Inference` class, the `PostProcess` class takes over to structure this information into a final, usable format. This stage is crucial for transforming processed data and model predictions into actionable reports.

The main steps in the postprocessing workflow, primarily handled by the `PostProcess` class, are:

1.  **Report Template Creation**:
    *   The process often begins by defining or loading a structured report template. This template dictates the layout and fields of the final output. While not explicitly a method, `PostProcess` is designed to work with such templates to ensure consistency in reporting.

2.  **Autofilling Report Fields**:
    *   The `PostProcess.autofill()` method is a key component here. It systematically populates the fields within the report template.
    *   This method draws data from multiple sources:
        *   **Raw Notes**: Basic information like patient identifiers, demographics, and direct quotes or sections from the original notes might be pulled in.
        *   **Inference Results**: The bulk of the structured data comes from the outputs of the `Inference` class. This includes classifications (e.g., CHIRPP case status), summaries, and extracted entities (like intent, substance use, location, etc.).
    *   The `autofill` logic intelligently maps these varied pieces of information to their respective fields in the report.

3.  **Final Report Generation**:
    *   Once all relevant fields are populated, the `PostProcess.create_report()` method is called.
    *   This method compiles all the autofilled data and generates the final report in a user-friendly format. While the exact output format can vary, a common example would be an Excel spreadsheet, which is suitable for review, analysis, and distribution. Other formats like structured text files or database entries are also possible.

The `Cases` table (aliased as `chirpp_report` in the database schema) is a likely representation of the structured data that results from this postprocessing, containing many of the fields that would be autofilled and then presented in a report.

Regarding the `chirpp.postprocess.events.Event` class: While its primary role is to represent and search for specific occurrences within notes (which can be a specialized form of postprocessing), its direct involvement in the main report generation pipeline handled by `PostProcess` might be more for specialized queries or custom report sections that focus on event-based data rather than the overarching case summary. For standard reporting, the `PostProcess` class is the main actor. The `SchemaError` exception, associated with the `Event` class, ensures data integrity if event data is being incorporated.
