
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

# Function to create a base map
def create_base_map(cities, mean_centroid):
    base_map = px.choropleth_mapbox(
        cities,
        geojson=cities.__geo_interface__,
        locations=cities.index,
        color=None,  # No specific color scaling
        mapbox_style='open-street-map',
        opacity=0.21,
        center={'lat': mean_centroid.y - 0.05, 'lon': mean_centroid.x},
        zoom=7.7
    )
    base_map.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    base_map.update_layout(height=600)  # Set height to 600px

    return base_map

# Load shapefile for cities
cities = gpd.read_file('/Users/taitai/Downloads/City_and_Unincorporated_Boundaries_(Legal)/City_and_Unincorporated_Boundaries_(Legal).shp')

# Load crime data for 2023 initially
crime_df = pd.read_csv('/Users/taitai/Downloads/2023crimedata.csv')
crime_df.columns = crime_df.columns.str.lower()

# Standardize category data format
crime_df['category'] = crime_df['category'].str.strip()

# Convert crime data to GeoDataFrame
crime_df['geometry'] = crime_df.apply(lambda row: Point(row.longitude, row.latitude), axis=1)
crime_data = gpd.GeoDataFrame(crime_df, geometry='geometry')

# Check and set CRS for crime_data
if crime_data.crs is None:
    crime_data.crs = "EPSG:4326"

# Convert cities CRS to match crime_data CRS
cities = cities.to_crs(crime_data.crs)

# Perform spatial join
joined_data = gpd.sjoin(crime_data, cities, how='inner', predicate='within')

# Calculate mean centroid
mean_centroid = cities.unary_union.centroid

# Create Dash app
app = dash.Dash(__name__)

# Define app layout with tabs and year dropdown
app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='year-dropdown',
            options=[
                {'label': str(year), 'value': str(year)} for year in range(2019, 2024)
            ],
            value='2023',  # Set default year value
            style={'width': '100%', 'margin-bottom': '10px'}
        ),
    ]),
    dcc.Tabs([
        # Tab 1: Heat Map and Choropleth
        dcc.Tab(label='LA County Crime Heat Map', children=[
            html.Div([
                dcc.Graph(id='heat-map-choropleth')
            ])
        ]),
        # Tab 2: Aggregated Crime Categories
        dcc.Tab(label='View by Aggregated Crime', children=[
            dcc.Checklist(
                id='crime-category-checklist',
                options=[
                    {'label': 'Person-Related Crimes', 'value': 'Person-Related Crimes'},
                    {'label': 'Property Crimes', 'value': 'Property Crimes'},
                    {'label': 'Drug and Alcohol-Related Crimes', 'value': 'Drug and Alcohol-Related Crimes'},
                    {'label': 'Miscellaneous Crimes', 'value': 'Miscellaneous Crimes'}
                ],
                value=['Person-Related Crimes', 'Property Crimes', 'Drug and Alcohol-Related Crimes', 'Miscellaneous Crimes'],
                labelStyle={'display': 'block'}
            ),
            html.Div([
                dcc.Graph(
                    id='aggregated-crime-scatter',
                    style={'height': '600px', 'width': '100%'}
                ),
            ])
        ]),
        # Tab 3: Specific Crime Categories
        dcc.Tab(label='View By Specific Crime', children=[
            # Dropdown select multiple feature at the top
            dcc.Dropdown(
                id='specific-crime-dropdown',
                options=[{'label': category, 'value': category} for category in sorted(crime_df['category'].unique())],
                value=[],  # Set default selection
                multi=True,  # Allow multiple selections
                style={'width': '100%', 'margin-bottom': '5px'}  # Set width and add margin below
            ),
            # Container for graph
            html.Div([
                # Graph on the right side
                dcc.Graph(
                    id='specific-crime-scatter',
                    style={'height': '600px', 'width': '100%'}
                )
            ])
        ])
    ])
])

# Define callback function to update crime data based on selected year
@app.callback(
    Output('heat-map-choropleth', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_data(selected_year):
    # Load crime data for the selected year
    crime_file_path = f'/Users/taitai/Downloads/{selected_year}crimedata.csv'
    if os.path.exists(crime_file_path):
        crime_df = pd.read_csv(crime_file_path)
        crime_df.columns = crime_df.columns.str.lower()

        # Standardize category data format
        crime_df['category'] = crime_df['category'].str.strip()

        # Convert crime data to GeoDataFrame
        crime_df['geometry'] = crime_df.apply(lambda row: Point(row.longitude, row.latitude), axis=1)
        crime_data = gpd.GeoDataFrame(crime_df, geometry='geometry')

        # Check and set CRS for crime_data
        if crime_data.crs is None:
            crime_data.crs = "EPSG:4326"

        # Convert cities CRS to match crime_data CRS
        cities_ = cities.to_crs(crime_data.crs)

        # Perform spatial join
        joined_data = gpd.sjoin(crime_data, cities_, how='inner', predicate='within')

        # Calculate mean centroid
        mean_centroid = cities_.unary_union.centroid


        # Convert joined_data to EPSG:4326
        joined_data = joined_data.to_crs(crime_data.crs)

        # Extract latitude and longitude from joined_data geometry
        joined_data['lat'] = joined_data.geometry.y
        joined_data['lon'] = joined_data.geometry.x


        # Create base map for heat map and choropleth
        heat_map_choropleth = create_base_map(cities_, mean_centroid)
        heat_map_choropleth.add_trace(
            px.density_mapbox(
                crime_data,
                lat='latitude',
                lon='longitude',
                z=None,
                radius=4,
                mapbox_style='open-street-map',
                center={'lat': crime_data['latitude'].mean() + 0.15, 'lon': crime_data['longitude'].mean()},
                title=f'{selected_year} Los Angeles County Crime Data Heat Map',
                opacity=0.5,
                color_continuous_scale='YlOrRd',
                hover_data={'city': True, 'category': True},

            ).data[0]
        )
        return heat_map_choropleth
    else:
        # If data file for the selected year doesn't exist, return an empty figure
        return {}

# Define callback function for aggregated crime categories
@app.callback(
    Output('aggregated-crime-scatter', 'figure'),
    [Input('crime-category-checklist', 'value'),
     Input('year-dropdown', 'value')]  # Add year dropdown as input
)
def update_aggregated_crime_scatter(selected_categories, selected_year):
    # Load crime data for the selected year
    crime_file_path = f'/Users/taitai/Downloads/{selected_year}crimedata.csv'
    if os.path.exists(crime_file_path):
        crime_df = pd.read_csv(crime_file_path)
        crime_df.columns = crime_df.columns.str.lower()

    # Aggregate crime categories based on the input selection
    bins = [
        ["NON-AGGRAVATED ASSAULTS", "AGGRAVATED ASSAULT", "FORCIBLE RAPE", "ROBBERY", "CRIMINAL HOMICIDE",
         "SEX OFFENSES MISDEMEANORS", "SEX OFFENSES FELONIES", "OFFENSES AGAINST FAMILY", "WEAPON LAWS",
         "DISORDERLY CONDUCT"],
        ["GRAND THEFT AUTO", "LARCENY THEFT", "BURGLARY", "ARSON", "VANDALISM", "RECEIVING STOLEN PROPERTY",
         "FORGERY", "FRAUD AND NSF CHECKS"],
        ["NARCOTICS", "DRUNK / ALCOHOL / DRUGS", "LIQUOR LAWS", "DRUNK DRIVING VEHICLE / BOAT"],
        ["VEHICLE / BOATING LAWS", "MISDEMEANORS MISCELLANEOUS", "FELONIES MISCELLANEOUS", "WARRANTS",
         "VAGRANCY", "GAMBLING", "FEDERAL OFFENSES WITH MONEY", "FEDERAL OFFENSES W/O MONEY"]
    ]
    labels = ["Person-Related Crimes", "Property Crimes", "Drug and Alcohol-Related Crimes", "Miscellaneous Crimes"]

# Create a new column 'aggregated_category' and assign labels based on crime categories
    def assign_aggregated_category(row):
     for bin_list, label in zip(bins, labels):
          if row['category'] in bin_list:
             return label
     return 'Other'


    crime_df['aggregated_category'] = crime_df.apply(assign_aggregated_category, axis=1)

     # Filter the crime data based on the selected categories
    filtered_data = crime_df[crime_df['aggregated_category'].isin(selected_categories)]


    # Create the base map using the provided `create_base_map` function
    fig = create_base_map(cities, mean_centroid)

    # Update the base map traces to hide the legend
    fig.update_traces(showlegend=False)

    # Create the scatter plot using Plotly Express
    scatter_plot = px.scatter_mapbox(
        filtered_data,
        lat='latitude',
        lon='longitude',
        color='aggregated_category',
        mapbox_style='open-street-map',
        zoom=7.7,
        hover_data={'city': True, 'category': True},  # Include year in hover data
        title='Aggregated Crime Categories Scatter Plot',
        opacity=0.5
    )

    # Add the scatter plot layer to the base map
    for trace in scatter_plot.data:
        fig.add_trace(trace)

      # Center the legend in the right side
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='bottom',
            xanchor='right',
            y=0.45,
            x=0.99
        )
    )


    return fig

# Define callback function for specific crime categories
@app.callback(
    Output('specific-crime-scatter', 'figure'),
    [Input('specific-crime-dropdown', 'value')],
     Input('year-dropdown', 'value')  # Add year dropdown as input
)
def update_specific_crime_scatter(selected_crime_categories, selected_year):
    # Load crime data for the selected year
    crime_file_path = f'/Users/taitai/Downloads/{selected_year}crimedata.csv'
    if os.path.exists(crime_file_path):
        crime_df = pd.read_csv(crime_file_path)
        crime_df.columns = crime_df.columns.str.lower()

        # Filter the crime data based on the selected crime categories
        filtered_data = crime_df[crime_df['category'].isin(selected_crime_categories)]

    # Create the base map using the provided `create_base_map` function
    fig = create_base_map(cities, mean_centroid)

    # Update the base map traces to hide the legend
    fig.update_traces(showlegend=False)
    # Create the scatter plot using Plotly Express
    scatter_plot = px.scatter_mapbox(
        filtered_data,
        lat='latitude',
        lon='longitude',
        color='category',
        mapbox_style='open-street-map',
        zoom=7.7,
        hover_data={'city': True, 'category': True},
        title='Specific Crime Categories Scatter Plot',
        opacity=0.5
    )

    # Add the scatter plot layer to the base map
    for trace in scatter_plot.data:
        fig.add_trace(trace)

# Update the layout to position the legend on the right side
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='bottom',
            xanchor='right',
            y=0.60,
            x=0.99
        ))

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


'''import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

# Function to create a base map
def create_base_map(cities, mean_centroid):
    base_map = px.choropleth_mapbox(
        cities,
        geojson=cities.__geo_interface__,
        locations=cities.index,
        color=None,  # No specific color scaling
        mapbox_style='open-street-map',
        opacity=0.21,
        center={'lat': mean_centroid.y - 0.05, 'lon': mean_centroid.x},
        zoom=7.7
    )
    base_map.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
    base_map.update_layout(height=600)  # Set height to 600px

    return base_map

# Load shapefile for cities
cities = gpd.read_file('/Users/taitai/Downloads/City_and_Unincorporated_Boundaries_(Legal)/City_and_Unincorporated_Boundaries_(Legal).shp')
print(cities.columns)
print(cities["CITY_NAME"].head())
# Load crime data for 2023 initially
crime_df = pd.read_csv('/Users/taitai/Downloads/2023crimedata.csv')
crime_df.columns = crime_df.columns.str.lower()
print(cities.crs)
# Standardize category data format
crime_df['category'] = crime_df['category'].str.strip()

# Convert crime data to GeoDataFrame
crime_df['geometry'] = crime_df.apply(lambda row: Point(row.longitude, row.latitude), axis=1)
crime_data = gpd.GeoDataFrame(crime_df, geometry='geometry')

# Check and set CRS for crime_data
if crime_data.crs is None:
    crime_data.crs = "EPSG:4326"

# Convert cities CRS to match crime_data CRS
cities = cities.to_crs(crime_data.crs)

# Perform spatial join
joined_data = gpd.sjoin(crime_data, cities, how='inner', predicate='within')

# Calculate mean centroid
mean_centroid = cities.unary_union.centroid

# Load arrest rate data for years 2019 to 2023
arrest_data = {}
for year in range(2019, 2024):
    filename = f'/Users/taitai/Downloads/transformed{year}.csv'
    if os.path.exists(filename):
        data = pd.read_csv(filename)
        data.columns = data.columns.str.lower()
        arrest_data[year] = data

# Create Dash app
app = dash.Dash(__name__)

# Define app layout with tabs and year dropdown
app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='year-dropdown',
            options=[
                {'label': str(year), 'value': str(year)} for year in range(2019, 2024)
            ],
            value='2023',  # Set default year value
            style={'width': '100%', 'margin-bottom': '10px'}
        ),
    ]),
    dcc.Tabs([
        # Tab 1: Heat Map and Choropleth
        dcc.Tab(label='LA County Crime Heat Map', children=[
            html.Div([
                dcc.Graph(id='heat-map-choropleth')
            ])
        ]),
        # Tab 2: Aggregated Crime Categories
        dcc.Tab(label='View by Aggregated Crime', children=[
            dcc.Checklist(
                id='crime-category-checklist',
                options=[
                    {'label': 'Person-Related Crimes', 'value': 'Person-Related Crimes'},
                    {'label': 'Property Crimes', 'value': 'Property Crimes'},
                    {'label': 'Drug and Alcohol-Related Crimes', 'value': 'Drug and Alcohol-Related Crimes'},
                    {'label': 'Miscellaneous Crimes', 'value': 'Miscellaneous Crimes'}
                ],
                value=['Person-Related Crimes', 'Property Crimes', 'Drug and Alcohol-Related Crimes', 'Miscellaneous Crimes'],
                labelStyle={'display': 'block'}
            ),
            html.Div([
                dcc.Graph(
                    id='aggregated-crime-scatter',
                    style={'height': '600px', 'width': '100%'}
                ),
            ])
        ]),
        # Tab 3: Specific Crime Categories
        dcc.Tab(label='View By Specific Crime', children=[
            # Dropdown select multiple feature at the top
            dcc.Dropdown(
                id='specific-crime-dropdown',
                options=[],
                value=[],  # Set default selection
                multi=True,  # Allow multiple selections
                style={'width': '100%', 'margin-bottom': '5px'}  # Set width and add margin below
            ),
            # Container for graph
            html.Div([
                # Graph on the right side
                dcc.Graph(
                    id='specific-crime-scatter',
                    style={'height': '600px', 'width': '100%'}
                )
            ])
        ]),
        # Tab 4: Arrest Rate Data Map
        dcc.Tab(label='Arrest Rate Data Map', children=[
            html.Div([
                dcc.Graph(id='arrest-rate-map')
            ])
        ])
    ])
])

# Define callback function to update crime data based on selected year
@app.callback(
    Output('heat-map-choropleth', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_data(selected_year):
    # Load crime data for the selected year
    crime_file_path = f'/Users/taitai/Downloads/{selected_year}crimedata.csv'
    if os.path.exists(crime_file_path):
        crime_df = pd.read_csv(crime_file_path)
        crime_df.columns = crime_df.columns.str.lower()

        # Standardize category data format
        crime_df['category'] = crime_df['category'].str.strip()

        # Convert crime data to GeoDataFrame
        crime_df['geometry'] = crime_df.apply(lambda row: Point(row.longitude, row.latitude), axis=1)
        crime_data = gpd.GeoDataFrame(crime_df, geometry='geometry')

        # Check and set CRS for crime_data
        if crime_data.crs is None:
            crime_data.crs = "EPSG:4326"

        # Convert cities CRS to match crime_data CRS
        cities_ = cities.to_crs(crime_data.crs)

        # Perform spatial join
        joined_data = gpd.sjoin(crime_data, cities_, how='inner', predicate='within')

        # Calculate mean centroid
        mean_centroid = cities_.unary_union.centroid


        # Convert joined_data to EPSG:4326
        joined_data = joined_data.to_crs(crime_data.crs)

        # Extract latitude and longitude from joined_data geometry
        joined_data['lat'] = joined_data.geometry.y
        joined_data['lon'] = joined_data.geometry.x


        # Create base map for heat map and choropleth
        heat_map_choropleth = create_base_map(cities_, mean_centroid)
        heat_map_choropleth.add_trace(
            px.density_mapbox(
                crime_data,
                lat='latitude',
                lon='longitude',
                z=None,
                radius=4,
                mapbox_style='open-street-map',
                center={'lat': crime_data['latitude'].mean() + 0.15, 'lon': crime_data['longitude'].mean()},
                title=f'{selected_year} Los Angeles County Crime Data Heat Map',
                opacity=0.5,
                color_continuous_scale='YlOrRd',
                hover_data={'city': True, 'category': True},

            ).data[0]
        )
        return heat_map_choropleth
    else:
        # If data file for the selected year doesn't exist, return an empty figure
        return {}

# Define callback function for aggregated crime categories
@app.callback(
    Output('aggregated-crime-scatter', 'figure'),
    [Input('crime-category-checklist', 'value')]
)
def update_aggregated_crime_scatter(selected_categories):
    # Aggregate crime categories based on the input selection
    bins = [
        ["NON-AGGRAVATED ASSAULTS", "AGGRAVATED ASSAULT", "FORCIBLE RAPE", "ROBBERY", "CRIMINAL HOMICIDE",
         "SEX OFFENSES MISDEMEANORS", "SEX OFFENSES FELONIES", "OFFENSES AGAINST FAMILY", "WEAPON LAWS",
         "DISORDERLY CONDUCT"],
        ["GRAND THEFT AUTO", "LARCENY THEFT", "BURGLARY", "ARSON", "VANDALISM", "RECEIVING STOLEN PROPERTY",
         "FORGERY", "FRAUD AND NSF CHECKS"],
        ["NARCOTICS", "DRUNK / ALCOHOL / DRUGS", "LIQUOR LAWS", "DRUNK DRIVING VEHICLE / BOAT"],
        ["VEHICLE / BOATING LAWS", "MISDEMEANORS MISCELLANEOUS", "FELONIES MISCELLANEOUS", "WARRANTS",
         "VAGRANCY", "GAMBLING", "FEDERAL OFFENSES WITH MONEY", "FEDERAL OFFENSES W/O MONEY"]
    ]
    labels = ["Person-Related Crimes", "Property Crimes", "Drug and Alcohol-Related Crimes", "Miscellaneous Crimes"]

# Create a new column 'aggregated_category' and assign labels based on crime categories
    def assign_aggregated_category(row):
     for bin_list, label in zip(bins, labels):
          if row['category'] in bin_list:
             return label
     return 'Other'

    crime_data['aggregated_category'] = crime_data.apply(assign_aggregated_category, axis=1)
    # Filter the crime data based on the selected categories
    filtered_data = crime_data[crime_data['aggregated_category'].isin(selected_categories)]

    # Create the base map using the provided `create_base_map` function
    fig = create_base_map(cities, mean_centroid)

    # Update the base map traces to hide the legend
    fig.update_traces(showlegend=False)

    # Create the scatter plot using Plotly Express
    scatter_plot = px.scatter_mapbox(
        filtered_data,
        lat='latitude',
        lon='longitude',
        color='aggregated_category',
        mapbox_style='open-street-map',
        zoom=7.7,
        hover_data={'city': True, 'category': True},  # Include year in hover data
        title='Aggregated Crime Categories Scatter Plot',
        opacity=0.5
    )

    # Add the scatter plot layer to the base map
    for trace in scatter_plot.data:
        fig.add_trace(trace)

      # Center the legend in the right side
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='bottom',
            xanchor='right',
            y=0.45,
            x=0.99
        )
    )


    return fig

# Define callback function for specific crime categories
@app.callback(
    Output('specific-crime-scatter', 'figure'),
    [Input('specific-crime-dropdown', 'value')]
)
def update_specific_crime_scatter(selected_crime_categories):
    # Filter the crime data based on the selected crime categories
    filtered_data = crime_data[crime_data['category'].isin(selected_crime_categories)]

    # Create the base map using the provided `create_base_map` function
    fig = create_base_map(cities, mean_centroid)

    # Update the base map traces to hide the legend
    fig.update_traces(showlegend=False)
    # Create the scatter plot using Plotly Express
    scatter_plot = px.scatter_mapbox(
        filtered_data,
        lat='latitude',
        lon='longitude',
        color='category',
        mapbox_style='open-street-map',
        zoom=7.7,
        hover_data={'city': True, 'category': True},
        title='Specific Crime Categories Scatter Plot',
        opacity=0.5
    )

    # Add the scatter plot layer to the base map
    for trace in scatter_plot.data:
        fig.add_trace(trace)

# Update the layout to position the legend on the right side
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='bottom',
            xanchor='right',
            y=0.60,
            x=0.99
        ))

    return fig


# Define callback function to update arrest rate data map based on selected year
@app.callback(
    Output('arrest-rate-map', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_arrest_rate_map(selected_year):
    print(arrest_data[int(selected_year)].columns)
    print(arrest_data[int(selected_year)].head())

    # Check if data for the selected year exists

    if int(selected_year) in arrest_data:
        # Merge arrest rate data with cities GeoDataFrame
        merged_data = pd.merge(cities, arrest_data[int(selected_year)], left_on='CITY_NAME', right_on='city', how='left')


        # Fill NaN values in 'Arrest Rate' column with a default value, such as 0
        merged_data['arrest rate'].fillna(0, inplace=True)

        # Handle nulls or non-matching cities in the merge
        # Filter out rows where the geometry is null
        merged_data = merged_data[merged_data['geometry'].notnull()]

        # Create base map for arrest rate data
        arrest_rate_map = create_base_map(merged_data, mean_centroid)

        # Add choropleth layer for arrest rate data
        arrest_rate_map.add_trace(
            px.choropleth_mapbox(
                merged_data,
                locations=merged_data.index,
                color='arrest rate',
                mapbox_style='open-street-map',
                opacity=0.6,
                color_continuous_scale='Viridis',
                hover_data={'CITY': True, 'arrest rate': True}
            ).data[0]
        )
        print(merged_data.columns)

        return arrest_rate_map
    else:
        # Return an empty figure if data for the selected year is not available
        return {}


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
    '''