# CLAIMM Data Files Documentation

This document describes the JSON data files generated from analyzing NETL's EDX CLAIMM (Critical Minerals and Materials) collection.

**Generated:** January 4, 2026
**Source:** https://edx.netl.doe.gov
**Total Datasets Analyzed:** 201
**Total Columns Discovered:** 17,361

---

## File Overview

| File | Size | Description |
|------|------|-------------|
| `claimm_datasets.json` | 554 KB | Raw dataset inventory from EDX API |
| `claimm_datasets_enhanced.json` | 561 KB | Datasets with category classification |
| `claimm_schema.json` | 7.2 KB | JSON Schema (2020-12) for dataset structure |
| `claimm_field_schemas.json` | 137 KB | Extracted field dictionaries (764 fields) |
| `claimm_all_schemas.json` | 2.2 MB | Auto-extracted schemas from all CSV files |
| `claimm_metadata_summary.json` | 21 KB | Metadata availability analysis |
| `claimm_complete_schema_report.json` | 39 KB | Comprehensive schema report |
| `schema_documentation_report.json` | 56 KB | Documentation gap analysis |

---

## Detailed File Descriptions

### 1. claimm_datasets.json

**Purpose:** Complete inventory of all 201 CLAIMM datasets from EDX.

**Structure:**
```json
[
  {
    "id": "uuid",
    "name": "url-safe-name",
    "title": "Human Readable Title",
    "notes": "Description text...",
    "author": "Author name or null",
    "organization": "Organization name or null",
    "tags": ["tag1", "tag2"],
    "metadata_created": "2024-01-15T10:30:00.000000",
    "metadata_modified": "2024-06-20T14:45:00.000000",
    "resources": [
      {
        "id": "resource-uuid",
        "name": "filename.csv",
        "description": "Resource description",
        "format": "CSV",
        "size": 1048576,
        "url": "https://...",
        "created": "2024-01-15T10:30:00",
        "last_modified": "2024-06-20T14:45:00"
      }
    ]
  }
]
```

**Usage:**
```python
import json
with open('claimm_datasets.json') as f:
    datasets = json.load(f)

# Find datasets by title
lithium_datasets = [d for d in datasets if 'lithium' in d['title'].lower()]
```

---

### 2. claimm_datasets_enhanced.json

**Purpose:** Same as above, plus category classification for each dataset.

**Additional Field:**
```json
{
  "category": "Rare Earth Elements"
}
```

**Categories:**
- Rare Earth Elements (57 datasets)
- Produced Water & NEWTS (20 datasets)
- Geology & Geophysics (24 datasets)
- Geographic/GIS (18 datasets)
- Mine Waste & Mining (18 datasets)
- Geochemistry (14 datasets)
- Coal & Coal Byproducts (12 datasets)
- Tools & Models (11 datasets)
- Infrastructure (1 dataset)
- Carbon Storage (1 dataset)
- Other (25 datasets)

**Usage:**
```python
import json
with open('claimm_datasets_enhanced.json') as f:
    datasets = json.load(f)

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for d in datasets:
    by_category[d['category']].append(d)
```

---

### 3. claimm_schema.json

**Purpose:** JSON Schema (draft 2020-12) defining the structure of CLAIMM datasets.

**Usage:** Validate dataset JSON against this schema using any JSON Schema validator.

```python
from jsonschema import validate
import json

with open('claimm_schema.json') as f:
    schema = json.load(f)

with open('claimm_datasets.json') as f:
    datasets = json.load(f)

for dataset in datasets:
    validate(instance=dataset, schema=schema)
```

**Key Definitions:**
- `Resource` - File/resource within a dataset
- `TagCategory` - Common tags used in CLAIMM

---

### 4. claimm_field_schemas.json

**Purpose:** Detailed field dictionaries extracted from datasets that include schema documentation.

**Structure:**
```json
{
  "PA_DEP_26r_Produced_Water": {
    "source": "Pennsylvania Department of Environmental Protection...",
    "total_fields": 251,
    "fields": [
      {
        "name": "Date_Collected",
        "format": "DATE",
        "unit": "MM/DD/YYYY",
        "definition": "Date that the sample was collected..."
      }
    ]
  },
  "NEWTS_Integrated_Dataset": {
    "source": "NEWTS Integrated Dataset (version 1.0)",
    "total_fields": 468,
    "fields": [
      {
        "index": 1,
        "csv_name": "C12H8N2",
        "fc_name": "C12H8N2",
        "alias": "1,10-Phenanthroline (mg/L)",
        "description": "1,10-Phenanthroline (mg/L)"
      }
    ]
  },
  "CMM_Insights": {
    "source": "United States CMM Insights Dataset",
    "total_fields": 45,
    "fields": [
      {
        "feature_id": "81",
        "feature_name": "asian population percentage",
        "feature_type": "census",
        "description": "Estimated percentage..."
      }
    ]
  }
}
```

**Datasets with Field Dictionaries:**
- NEWTS Integrated Dataset - 468 fields (water chemistry)
- PA DEP 26r Produced Water - 251 fields (geochemical)
- CMM Insights - 45 fields (census/infrastructure)

---

### 5. claimm_all_schemas.json

**Purpose:** Auto-extracted column headers and types from all 55 CSV files.

**Structure:**
```json
{
  "summary": {
    "total_resources": 114,
    "successful": 55,
    "failed": 59,
    "total_columns_discovered": 17361
  },
  "schemas": [
    {
      "resource_id": "uuid",
      "resource_name": "data.csv",
      "format": "CSV",
      "dataset_id": "dataset-uuid",
      "dataset_title": "Dataset Title",
      "category": "Produced Water & NEWTS",
      "column_count": 192,
      "headers": ["Column1", "Column2", "..."],
      "column_types": [
        {
          "name": "Column1",
          "type": "string",
          "nullable": false,
          "sample_values": ["value1", "value2"]
        }
      ]
    }
  ],
  "failed_resources": [
    {
      "resource_id": "uuid",
      "resource_name": "file.xlsx",
      "format": "XLSX",
      "error": "Excel parse error..."
    }
  ]
}
```

**Column Types Detected:**
- `string` - Text values
- `integer` - Whole numbers
- `float` - Decimal numbers
- `date` - Date values (YYYY-MM-DD format)
- `datetime` - Date and time values
- `boolean` - True/False values
- `unknown` - Could not determine type

**Usage:**
```python
import json
with open('claimm_all_schemas.json') as f:
    data = json.load(f)

# Find schemas with specific columns
for schema in data['schemas']:
    if 'lithium' in ' '.join(schema['headers']).lower():
        print(f"{schema['resource_name']}: {schema['column_count']} columns")
```

---

### 6. claimm_metadata_summary.json

**Purpose:** Analysis of metadata availability across all datasets.

**Structure:**
```json
{
  "collection_overview": {
    "name": "CLAIMM - Critical Minerals and Materials",
    "total_datasets": 201,
    "total_resources": 517,
    "categories": {
      "Rare Earth Elements": {"count": 57, "resources": 129}
    }
  },
  "metadata_availability": {
    "dataset_level": {
      "always_available": ["id", "name", "title", "notes", "tags"],
      "sometimes_available": ["author", "organization", "doi"]
    },
    "resource_level": {
      "always_available": ["id", "name", "format", "url"],
      "sometimes_available": ["description", "size", "hash"]
    }
  },
  "data_formats": {
    "CSV": {"count": 55, "unique_datasets": 16},
    "HTML": {"count": 151, "unique_datasets": 103}
  },
  "field_dictionaries": {...},
  "schema_availability_by_dataset": [...]
}
```

---

### 7. claimm_complete_schema_report.json

**Purpose:** Comprehensive summary of schema extraction results.

**Structure:**
```json
{
  "title": "CLAIMM Complete Schema Documentation Report",
  "generated": "2026-01-04",
  "summary": {
    "total_datasets": 201,
    "datasets_with_tabular_data": 16,
    "total_tabular_resources": 55,
    "total_columns_discovered": 17361,
    "datasets_with_field_dictionaries": 3,
    "total_documented_fields": 764
  },
  "schema_coverage": {
    "by_category": {
      "Produced Water & NEWTS": {
        "datasets": 10,
        "resources": 48,
        "columns": 16433
      }
    }
  },
  "column_statistics": {
    "most_common_columns": [
      {"name": "sample_description", "occurrences": 25}
    ],
    "largest_datasets": [
      {
        "resource_name": "GWB_4majors_min_15000MostComplete_Transpose.csv",
        "column_count": 1862
      }
    ]
  },
  "documentation_status": {
    "with_field_dictionary": [...],
    "auto_extracted_only": [...],
    "no_tabular_data": [...]
  }
}
```

---

### 8. schema_documentation_report.json

**Purpose:** Identifies datasets lacking schema documentation.

**Structure:**
```json
{
  "summary": {
    "total_datasets": 201,
    "with_schema_docs": 43,
    "without_schema_docs": 158,
    "coverage_percentage": 21.4
  },
  "without_schema_by_category": {
    "Rare Earth Elements": 46,
    "Geology & Geophysics": 22
  },
  "priority_datasets_missing_schema": [
    {
      "id": "uuid",
      "title": "Dataset Title",
      "category": "Category",
      "data_files": 9,
      "formats": ["CSV", "XLSX"],
      "sample_files": ["file1.csv", "file2.xlsx"]
    }
  ],
  "datasets_without_schema": [...]
}
```

**Usage:** Identify datasets that need documentation:
```python
import json
with open('schema_documentation_report.json') as f:
    report = json.load(f)

# Prioritize datasets with most data files but no docs
for ds in report['priority_datasets_missing_schema'][:10]:
    print(f"{ds['title']}: {ds['data_files']} files, formats: {ds['formats']}")
```

---

## Common Queries

### Find all CSV files with their schemas
```python
import json

with open('claimm_all_schemas.json') as f:
    data = json.load(f)

for schema in data['schemas']:
    print(f"{schema['resource_name']}: {schema['column_count']} columns")
```

### Get datasets by category
```python
import json
from collections import defaultdict

with open('claimm_datasets_enhanced.json') as f:
    datasets = json.load(f)

by_cat = defaultdict(list)
for d in datasets:
    by_cat[d['category']].append(d['title'])

for cat, titles in by_cat.items():
    print(f"\n{cat} ({len(titles)} datasets):")
    for t in titles[:3]:
        print(f"  - {t}")
```

### Find columns by name pattern
```python
import json
import re

with open('claimm_all_schemas.json') as f:
    data = json.load(f)

pattern = re.compile(r'lithium|Li', re.IGNORECASE)

for schema in data['schemas']:
    matching = [h for h in schema['headers'] if pattern.search(h)]
    if matching:
        print(f"{schema['resource_name']}:")
        for col in matching:
            print(f"  - {col}")
```

---

## Data Sources

All data was extracted from NETL's Energy Data eXchange (EDX) via the CKAN API:
- API Base: `https://edx.netl.doe.gov/api/3/action/`
- CLAIMM Portal: `https://edx.netl.doe.gov/edxapps/claimm/`

---

## License

Data sourced from public U.S. Government datasets. Individual dataset licenses vary - check the `license_type` field in resource metadata.
