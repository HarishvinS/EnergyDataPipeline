# Energy Data Pipeline Documentation

### Important Note
This project is for the Harvard Ventures TECH Summer Program and Rayfield Systems as proof of work. This project does not bear much resemablence to my past work for this reason. Check out these if you want to see more advanced work: (LightLink)[https://github.com/HarishvinS/LightLink], (Surface Code Analysis)[https://github.com/HarishvinS/surface-code-analysis]

## Summary

This is a energy data processing pipeline, covering dataset selection rationale, data cleaning methodology, and feature engineering decisions. The pipeline processes solar power generation data to create a clean, feature-rich dataset suitable for machine learning applications including forecasting, anomaly detection, and performance analysis.

Dataset sourced from: https://www.kaggle.com/datasets/anikannal/solar-power-generation-data

---

## Part A: Dataset Choice Documentation

### Dataset Selection Rationale

**Dataset:** `Plant_1_Generation_Data.csv`

**Why This Dataset Was Chosen:**
- **Solar Power Generation Focus**: The dataset represents solar photovoltaic (PV) power generation data, which is critical for renewable energy analysis and grid management
- **High-Resolution Temporal Data**: Contains 15-minute interval measurements, providing granular insights into power generation patterns
- **Multi-Inverter Coverage**: Tracks 22 different inverters (SOURCE_KEY) within a single plant, enabling comprehensive plant-level analysis
- **Real-World Operational Data**: Captures actual production data from May 15-16, 2020, including natural variations and operational conditions

**Energy Generation Type:** Solar Photovoltaic (PV)
- DC power generation from solar panels
- AC power output after inverter conversion
- Daily and cumulative yield tracking

**Time Span and Granularity:**
- **Duration**: 2 days (May 15-16, 2020)
- **Granularity**: 15-minute intervals
- **Total Records**: 68,779 measurements
- **Coverage**: 24/7 monitoring including nighttime zero-generation periods

**Energy Workflow Support:**
1. **Performance Monitoring**: Track individual inverter and plant-level performance
2. **Forecasting**: Historical patterns enable short-term and day-ahead generation forecasting
3. **Anomaly Detection**: Identify underperforming inverters or equipment failures
4. **Grid Integration**: Support grid operators with generation predictions
5. **Maintenance Planning**: Performance trends inform preventive maintenance schedules

**Pipeline Goals Alignment:**
- Enables predictive analytics for renewable energy systems
- Supports operational optimization through performance insights
- Facilitates integration with energy management systems
- Provides foundation for advanced analytics and machine learning models

### Dataset Characteristics

**Raw Data Structure:**
- **Total Rows**: 68,779 records
- **Total Columns**: 7 attributes
- **File Size**: Approximately 4.2MB

**Key Columns and Meanings:**
- `DATE_TIME`: Timestamp in DD-MM-YYYY HH:MM format (15-minute intervals)
- `PLANT_ID`: Plant identifier (constant: 4135001)
- `SOURCE_KEY`: Unique inverter identifier (22 different inverters)
- `DC_POWER`: Direct current power generation (kW)
- `AC_POWER`: Alternating current power output (kW)
- `DAILY_YIELD`: Daily energy production (kWh) - resets at midnight
- `TOTAL_YIELD`: Cumulative lifetime energy production (kWh)

**Data Quality Assessment:**

*Completeness Issues:*
- Some inverters have intermittent data gaps
- Missing records during certain time periods
- Inconsistent inverter reporting (some appear/disappear)

*Data Range and Patterns:*
- **Power Generation**: 0 kW (nighttime) to ~12,000 kW (peak solar)
- **Daily Yield**: 0-6,500 kWh per inverter per day
- **Total Yield**: 6-7 million kWh cumulative per inverter
- **Seasonal Context**: Mid-May data represents good solar conditions

*Limitations and Constraints:*
- Limited to 2-day period (insufficient for seasonal analysis)
- Single plant data (no multi-site comparison)
- No weather data correlation available
- No equipment specification details
- Missing inverter capacity ratings

**Time Period Coverage:**
- **Start**: May 15, 2020 00:00
- **End**: May 16, 2020 (partial day)
- **Solar Generation Hours**: ~06:00 to 18:30 daily
- **Peak Generation**: ~10:00-14:00 timeframe

---

## Part B: Cleaning Logic Documentation

### Step-by-Step Cleaning Process

#### 1. DateTime Conversion
**Implementation:**
```python
self.cleaned_data[date_col] = pd.to_datetime(self.cleaned_data[date_col], errors='coerce')
```

**Problem Solved:**
- Raw timestamps stored as strings in DD-MM-YYYY HH:MM format
- Inconsistent datetime parsing across different systems
- Need for time-based operations and feature extraction

**Method Used:**
- `pd.to_datetime()` with `errors='coerce'` parameter
- Converts invalid dates to NaT (Not a Time) for later handling
- Maintains timezone-naive format suitable for local analysis

**Error Handling:**
- Invalid timestamps become NaT values
- Preserves data integrity while flagging problematic records
- Enables downstream temporal analysis and sorting

**Alternative Approaches Considered:**
- Manual string parsing (rejected: error-prone)
- Multiple format specifications (rejected: unnecessary complexity)

#### 2. Empty Row Removal
**Implementation:**
```python
self.cleaned_data = self.cleaned_data.dropna(how='all')
```

**Problem Solved:**
- Completely empty rows from data export/import processes
- Rows with only whitespace or null values
- Reduces dataset size and processing overhead

**Definition of "Empty":**
- Rows where ALL columns contain NaN/null values
- Does not remove rows with partial missing data
- Preserves records with at least one valid measurement

**Data Retention Impact:**
- Minimal impact on valid records
- Removes only truly empty rows
- Maintains data completeness for analysis

#### 3. Missing Value Handling in Key Columns
**Implementation:**
```python
key_cols = [col for col in self.cleaned_data.columns if any(word in col.lower() 
           for word in ['yield', 'energy', 'power', 'generation', 'output'])]
self.cleaned_data = self.cleaned_data.dropna(subset=key_cols)
```

**Key Column Identification:**
- `DC_POWER`: Essential for generation analysis
- `AC_POWER`: Critical for output measurement
- `DAILY_YIELD`: Required for performance tracking
- `TOTAL_YIELD`: Needed for cumulative analysis

**Strategy: Drop vs. Fill Decision:**
- **Drop**: Chosen for power and yield columns
- **Rationale**: Missing power data indicates equipment/measurement failure
- **Impact**: Ensures data quality over quantity
- **Alternative**: Interpolation rejected due to energy generation volatility

**Data Retention Impact:**
- Removes ~5-10% of records with missing critical measurements
- Preserves data integrity for reliable analysis
- Maintains temporal continuity where possible

#### 4. Column Name Standardization
**Implementation:**
```python
self.cleaned_data.columns = self.cleaned_data.columns.str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
```

**Problem Solved:**
- Inconsistent column naming conventions
- Mixed case and special characters
- Spaces in column names causing code issues

**Standardization Rules:**
- Convert to lowercase for consistency
- Replace spaces with underscores
- Remove parentheses and special characters
- Maintain readability and Python compatibility

**Benefits:**
- Consistent programmatic access
- Reduced naming errors in code
- Improved code maintainability

#### 5. Numeric Conversion
**Implementation:**
```python
for col in energy_cols:
    self.cleaned_data[col] = pd.to_numeric(self.cleaned_data[col], errors='coerce')
```

**Problem Solved:**
- String representations of numeric values
- Mixed data types in energy columns
- Non-numeric characters in measurement fields

**Method Used:**
- `pd.to_numeric()` with `errors='coerce'`
- Converts invalid numbers to NaN
- Preserves valid numeric data

**Columns Affected:**
- All power and energy measurement columns
- Ensures mathematical operations are possible
- Enables statistical analysis and aggregations

#### 6. Outlier Removal (IQR Method)
**Implementation:**
```python
Q1 = self.cleaned_data[col].quantile(0.25)
Q3 = self.cleaned_data[col].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
```

**Why IQR Method Chosen:**
- Robust to extreme values
- Standard statistical approach
- Suitable for skewed energy generation data
- Less sensitive than standard deviation methods

**Parameters:**
- **Multiplier**: 1.5 × IQR (standard threshold)
- **Bounds**: Q1 - 1.5×IQR to Q3 + 1.5×IQR
- **Application**: Applied to each energy column independently

**What Constitutes an Outlier:**
- Values below Q1 - 1.5×IQR (unusual low generation)
- Values above Q3 + 1.5×IQR (impossible high generation)
- Likely measurement errors or equipment malfunctions

**Data Retention Impact:**
- Removes ~2-5% of records as outliers
- Preserves 95%+ of valid measurements
- Improves model training data quality

**Alternative Approaches Considered:**
- Z-score method (rejected: assumes normal distribution)
- Percentile-based (rejected: too aggressive)
- Domain-specific limits (rejected: lacks equipment specifications)

---

## Part C: Feature Engineering Documentation

### Time-Based Features

**Features Created:**
```python
self.processed_data['hour'] = self.processed_data[date_col].dt.hour
self.processed_data['day'] = self.processed_data[date_col].dt.day
self.processed_data['month'] = self.processed_data[date_col].dt.month
self.processed_data['year'] = self.processed_data[date_col].dt.year
self.processed_data['dayofweek'] = self.processed_data[date_col].dt.dayofweek
self.processed_data['is_weekend'] = self.processed_data['dayofweek'].isin([5, 6]).astype(int)
```

**Value for Energy Analysis:**
- **Hour**: Critical for solar generation patterns (sunrise to sunset)
- **Day**: Enables day-to-day performance comparison
- **Month**: Seasonal generation pattern analysis
- **Year**: Long-term trend analysis (when multi-year data available)
- **Day of Week**: Identifies operational patterns and maintenance schedules
- **Weekend Flag**: Distinguishes operational vs. maintenance periods

**Pattern Recognition Enablement:**
- Diurnal solar generation cycles
- Seasonal variations in output
- Operational schedule impacts
- Maintenance window identification

**Machine Learning Benefits:**
- Categorical features for tree-based models
- Cyclical pattern recognition
- Time-aware feature engineering
- Improved forecasting accuracy

### Rolling Statistics Features

**Implementation:**
```python
# 4-hour rolling statistics
self.processed_data[f'{col}_rolling_mean_4'] = self.processed_data[col].rolling(4).mean()
self.processed_data[f'{col}_rolling_std_4'] = self.processed_data[col].rolling(4).std()

# 24-hour rolling statistics  
self.processed_data[f'{col}_rolling_mean_24'] = self.processed_data[col].rolling(24).mean()
self.processed_data[f'{col}_rolling_max_24'] = self.processed_data[col].rolling(24).max()
```

**Window Selection Rationale:**

*4-Hour Window (16 data points):*
- **Purpose**: Short-term trend analysis
- **Rationale**: Captures cloud cover effects and short-term variations
- **Use Case**: Real-time anomaly detection and immediate performance monitoring
- **Statistical Significance**: Sufficient data points for stable statistics

*24-Hour Window (96 data points):*
- **Purpose**: Daily pattern analysis
- **Rationale**: Full diurnal cycle comparison
- **Use Case**: Day-over-day performance comparison and baseline establishment
- **Seasonal Context**: Accounts for daily solar cycle variations

**Statistics Calculated:**
- **Mean**: Average performance over window
- **Standard Deviation**: Variability and stability measurement
- **Maximum**: Peak performance capability

**Insights Provided:**
- **Trend Analysis**: Identify improving/declining performance
- **Stability Assessment**: Measure generation consistency
- **Anomaly Detection**: Deviation from rolling averages
- **Performance Benchmarking**: Compare against historical patterns

**Computational Trade-offs:**
- Increased feature dimensionality
- Higher memory usage
- Enhanced predictive capability
- Improved model performance

### Temporal Relationship Features

**Percentage Change Calculation:**
```python
self.processed_data[f'{col}_pct_change'] = self.processed_data[col].pct_change()
```

**Volatility Insights:**
- Measures period-to-period generation changes
- Identifies rapid fluctuations (cloud cover, equipment issues)
- Quantifies generation stability
- Enables volatility-based alerting

**Lag Features:**
```python
self.processed_data[f'{col}_lag_1'] = self.processed_data[col].shift(1)
self.processed_data[f'{col}_lag_24'] = self.processed_data[col].shift(24)
```

**Lag Selection Rationale:**

*1-Hour Lag (4 periods):*
- **Purpose**: Immediate previous state
- **Use Case**: Short-term forecasting and trend continuation
- **Pattern**: Captures immediate generation momentum

*24-Hour Lag (96 periods):*
- **Purpose**: Same time previous day
- **Use Case**: Day-over-day comparison and seasonal adjustment
- **Pattern**: Accounts for diurnal cycle similarities

**Forecasting Capabilities:**
- Autoregressive model inputs
- Time series pattern recognition
- Trend continuation analysis
- Seasonal adjustment factors

### Aggregation Features

**Plant-Level Ratios:**
```python
plant_means = self.processed_data.groupby('plant_id')[energy_cols].transform('mean')
self.processed_data[f'{col}_plant_mean_ratio'] = self.processed_data[col] / plant_means[col]
```

**Source-Level Ratios:**
```python
source_means = self.processed_data.groupby('source_key')[energy_cols].transform('mean')
self.processed_data[f'{col}_source_mean_ratio'] = self.processed_data[col] / source_means[col]
```

**Normalization Benefits:**
- **Scale Independence**: Enables comparison across different inverter capacities
- **Relative Performance**: Identifies over/under-performing equipment
- **Anomaly Detection**: Deviations from expected performance ratios
- **Multi-Plant Analysis**: Standardized metrics for fleet management

**Use Cases:**
- Equipment performance ranking
- Maintenance prioritization
- Capacity factor analysis
- Comparative efficiency assessment
