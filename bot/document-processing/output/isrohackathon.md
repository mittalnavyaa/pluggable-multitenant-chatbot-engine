# Urban Heat Action Planner
## AI-assisted Decision Support System for Urban Heat Mitigation
### 1. Background
Urban Heat Island (UHI) is becoming a major challenge for rapidly growing Indian cities due to increasing urbanization, reduction in green spaces, dense built-up areas and changing climatic conditions. High surface temperatures affect public health, increase electricity demand, reduce outdoor comfort and negatively impact overall urban sustainability.
Many Indian cities have already started implementing Heat Action Plans. For example, Ahmedabad introduced India's first Heat Action Plan and has promoted measures such as cool roofs and urban greening. Hyderabad has also piloted cool roof programmes for reducing heat exposure. Internationally, Singapore has adopted extensive urban greening, rooftop vegetation and "City in Nature" initiatives to reduce urban temperatures, while cities such as Los Angeles have implemented cool roofs and cool pavements in selected regions.
Although these interventions are already known, a major challenge still remains:
Which intervention should be implemented, where should it be implemented first, and why?
Today, this decision largely depends on manual analysis by planners and experts.
Our proposed system aims to simplify this decision-making process.

### 2. Existing Approaches and Their Limitations
Most existing studies focus on one part of the problem.
Some studies identify Urban Heat Island hotspots using satellite imagery.
Some build machine learning models to predict Land Surface Temperature.
Some analyze how vegetation or built-up areas affect temperature.
Municipal authorities then manually decide where tree plantation, cool roofs or other interventions should be implemented.
This creates three major limitations:
* Heat maps identify where the problem exists but not what action should be taken.
* The same intervention is often suggested for the entire city even though every locality has different characteristics.
* Existing studies rarely convert satellite observations into implementation-ready planning reports that municipal authorities can directly use.
Our solution addresses these limitations.

### 3. Proposed Solution
We propose an AI-assisted Urban Heat Action Planner, a planning support system that converts satellite observations into ward-level implementation plans.
Instead of treating the city as one large region, the system divides the city into small planning units (wards or grid cells). Every planning unit is analysed independently because each locality has different land use, vegetation, building density and weather conditions.
The proposed system will initially be demonstrated on Pune because it has rich OpenStreetMap coverage, freely available satellite imagery, rapid urbanization and diverse urban morphology. The same framework can later be applied to other Indian cities without major changes.
The complete workflow consists of six stages.

#### Stage 1 : Heat Mapping
The system first acquires satellite observations from Landsat and ECOSTRESS to generate Land Surface Temperature maps.
Using these maps, hotspots are identified across the city.
Instead of simply colouring the hottest regions, every hotspot is assigned to its corresponding ward or planning unit.
Example:
Ward 18
Current LST : 45.8°C
Heat Severity : Very High
Affected Area : 2.4 km²

#### Stage 2 : Heat Profile Generation
After hotspot identification, the system generates a Heat Profile for every ward.
The Heat Profile combines information from satellite imagery, weather datasets and urban infrastructure.
Each ward profile contains:
* Land Surface Temperature
* Vegetation Cover (NDVI)
* Built-up Density (NDBI)
* Road Density
* Building Density
* Impervious Surface
* Distance to Water Bodies
* Air Temperature
* Humidity
* Wind Speed
Instead of looking at multiple GIS layers separately, planners receive one consolidated Heat Profile for every ward.

#### Stage 3 : Heat Driver Analysis
This stage determines why a particular location is becoming hotter.
Rather than showing only the temperature, the system identifies the dominant contributors to heat.
Example
Ward 18
Primary Driver
Low Vegetation
Secondary Driver
High Impervious Surface
Third Driver
Dense Built-up Area
The contribution of different variables is explained using feature importance methods so that planners understand why the recommendation has been generated.

#### Stage 4 : Feasibility Analysis
This is one of the key components of the proposed system.
Instead of recommending interventions without considering ground conditions, the system first checks whether an intervention is actually feasible.
Using OpenStreetMap, land-use maps and satellite imagery, potential implementation locations are identified.
For Tree Plantation:
* Existing parks with sparse vegetation
* Road medians
* Vacant open land
* Canal and river buffer zones
For Cool Roofs:
* Government schools
* Municipal hospitals
* Bus depots
* Community centres
* Large public buildings
For Urban Greening:
* Vacant municipal land
* Institutional campuses
* Public parks
If a ward has very limited open space, the system does not recommend large-scale plantation and instead prioritizes cool roofs or reflective surfaces.
This makes the recommendations practical rather than generic.

#### Stage 5 : Scenario Evaluation
Once feasible intervention locations have been identified, different cooling scenarios are generated.
Examples:
Scenario 1
Increase roadside tree cover
Scenario 2
Implement cool roofs on selected public buildings
Scenario 3
Increase tree cover + cool roofs
Scenario 4
Increase green spaces
For each scenario, the environmental parameters are modified and the AI model estimates the expected reduction in Land Surface Temperature.
Instead of recommending only one solution, the system compares multiple alternatives before selecting the most suitable one.
Example
Current LST
45.8°C
Tree Plantation
42.9°C
Cool Roofs
43.5°C
Tree Plantation + Cool Roofs
41.8°C
The intervention with the highest expected impact and practical feasibility is selected.

#### Stage 6 : Urban Cooling Action Report
Instead of producing only a heat map, the system automatically generates a detailed planning report for every ward.
Example
WARD 18 COOLING ACTION REPORT
Current Heat Severity
Very High
Primary Heat Drivers
* Low Vegetation
* Dense Built-up Area
Recommended Intervention
Tree Plantation
Implementation Locations
* Municipal Park
* Road Medians
* Canal Buffer Zone
Estimated Cooling
2.9°C
Priority
Very High
Reason
Large plantation space available and high population exposure.
All ward reports are combined into a city-wide priority report that helps municipal authorities decide where limited budgets should be invested first.

### 4. System Outputs
The proposed system produces six practical outputs.
* City-wide Urban Heat Map
Shows hotspot distribution across the city.
* Ward Heat Profile
Summarizes all important environmental characteristics for every ward.
* Heat Driver Report
Explains why each hotspot exists.
* Feasibility Map
Highlights locations where different cooling interventions can realistically be implemented.
* Ward Cooling Action Report
Provides location-specific recommendations, estimated cooling impact and implementation priority.
* City Priority Report
Ranks wards based on heat severity, population exposure and expected cooling benefit.

### 5. Why This Solution Is Different
Existing studies mainly answer:
"Where is the city hot?"
Our system answers:
* Why is this ward hot?
* Which intervention is most suitable?
* Where can it actually be implemented?
* What cooling benefit is expected?
* Which wards should receive priority if the budget is limited?
Instead of producing another heat map, the proposed framework converts satellite observations into implementation-ready planning information.
The focus is not on developing a new cooling technology but on helping planners make better and faster decisions using existing technologies.

### 6. Unique Features
* Ward-wise Heat Profiles instead of only city-level heat maps.
* Automatic identification of dominant heat drivers.
* GIS-based feasibility analysis before recommending interventions.
* Comparison of multiple cooling scenarios.
* Location-specific recommendations instead of one solution for the whole city.
* Ward Cooling Action Reports for municipal authorities.
* City-wide priority ranking for budget allocation.
* Explainable recommendations with supporting reasons.
* Uses only publicly available datasets, making it scalable to other Indian cities.

### 7. Technology Stack
* Satellite Data
	+ Landsat 8/9
	+ ECOSTRESS
	+ Sentinel-2
* Weather
	+ ERA5
* Urban Data
	+ OpenStreetMap
	+ Global Human Settlement Layer (GHSL)
* GIS Processing
	+ Google Earth Engine
	+ QGIS
* Machine Learning
	+ Random Forest / XGBoost for Land Surface Temperature modelling
	+ SHAP for interpreting feature importance
* Backend
	+ Python
	+ FastAPI
* Frontend
	+ React
	+ Leaflet / MapLibre
* Database
	+ PostgreSQL with PostGIS

### 8. Feasibility
The proposed system is designed using only freely available datasets and widely used open-source tools.
No specialised hardware is required. The machine learning component uses structured environmental features rather than computationally intensive deep learning models, making the framework suitable for development on a standard laptop.
The project does not introduce new cooling technologies. Instead, it strengthens existing Heat Action Plans by providing a systematic and data-driven method to identify priority locations and suitable interventions.
This makes the proposed framework practical, scalable and suitable for pilot implementation in Indian cities.

### 9. Future Scope
The framework can later be extended by integrating:
* Real-time weather forecasts
* IoT temperature sensors
* Citizen heat complaints
* Budget-based intervention planning
* Multi-city comparison
* Seasonal heat monitoring
The same methodology can also be adapted for Smart City Mission projects and future urban climate resilience planning.

<!-- PAGE_NUMBER: 10 -->
Proposed System Workflow
Satellite Data + Weather Data + Urban Infrastructure Data
↓
Generate Land Surface Temperature Map
↓
Detect Urban Heat Hotspots
↓
Generate Ward-wise Heat Profiles
↓
Identify Dominant Heat Drivers
↓
Perform GIS-based Feasibility Analysis
↓
Generate Multiple Cooling Scenarios
↓
Predict Cooling Impact of Each Scenario
↓
Select Most Suitable Intervention
↓
Generate Ward Cooling Action Report
↓
Generate City Priority Report for Municipal Planning