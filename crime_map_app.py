import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

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
cities = gpd.read_file('City_and_Unincorporated_Boundaries_(Legal).shp')

# Load crime data
crime_df = pd.read_csv(''
                       '2023crimedata.csv')
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

# Convert joined_data to EPSG:4326
joined_data = joined_data.to_crs(crime_data.crs)

# Extract latitude and longitude from joined_data geometry
joined_data['lat'] = joined_data.geometry.y
joined_data['lon'] = joined_data.geometry.x


# Create Dash app
app = dash.Dash(__name__)


# Define app layout with tabs
app.layout = html.Div([
    dcc.Tabs([
        # Tab 1: Heat Map and Choropleth
        dcc.Tab(label='LA County 2023 Crime Heat Map', children=[
            html.Div(
    dcc.Graph(
        id='heat-map-choropleth',
        figure=create_base_map(cities, mean_centroid)
        .add_trace(
            px.density_mapbox(
                crime_data,
                lat='latitude',
                lon='longitude',
                z=None,
                radius=4,
                mapbox_style='open-street-map',
                center={'lat': crime_data['latitude'].mean() + 0.15, 'lon': crime_data['longitude'].mean()},
                title='2023 Los Angeles County Crime Data Heat Map',
                opacity=0.5,
                color_continuous_scale='YlOrRd',
                hover_data=['city', 'category']
            ).data[0]
        ),
        style={'height': '100%', 'width': '100%', 'margin': '0'}  # Adjust the style to remove margin
    ),
    style={'height': '100%', 'width': '100%', 'margin': '0', 'padding': '0'}  # Add these styles to html.Div

            )
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
        hover_data=['city', 'category'],
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
    [Input('specific-crime-dropdown', 'value')]  # Use the dropdown input instead of the checklist
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
        hover_data=['city', 'category'],
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
