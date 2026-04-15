#developed by Fouad Zablith

import streamlit as st
import pandas as pd
import pydeck as pdk
from PIL import Image

#load the data from excel in a dateframe
#a similar (with cleaner ) dataset is accessible online at https://docs.google.com/file/d/0B1k6zmQ4NXQlZ0dBcjFrNWhUSTA/edit
data = pd.read_excel(r'CholeraPumps_Deaths.xls')
df = pd.DataFrame(data, columns=['count','geometry'])

#clean and replace the coordinates data to fit the PyDeck map 
df = df.replace({'<Point><coordinates>': ''},regex=True )
df = df.replace({'</coordinates></Point>': ''},regex=True )

#create new longitude and latitude columns in dataframe
split = df['geometry'].str.split(',',n=1, expand=True)
df['lon'] = split[0].astype(float)
df['lat'] = split[1].astype(float)

df.drop(columns=['geometry'], inplace = True)

#st.write(df)

st.header('John Snow\'s 1854 Cholera Deaths Map in London')
st.subheader('This is a recreation of Snow\'s famous map that helped identifying the source of cholera oubreak in London')

#create a slider to filter the number of deaths
death_to_filter = st.slider('Number of Deaths', 0, 15, 2)  # min: 0 death, max: 15 deaths, default: 7 deaths
filtered_df = df[df['count'] >= death_to_filter]
st.subheader(f'Map of more than {death_to_filter} deaths')

#get the pumps location from the last 8 entries in the data (in the original data source, pumps were noted as having -999 death as a differentiator)
pumps_df = df[df['count'] == -999]

#checkbox to enable seeing the location of pumps
if(st.checkbox('Show pumps',value=True)):
    pump_radius = 5
else:
    pump_radius = 0

# CHANGE 1 done by Nour: add a metric summary
col1, col2 = st.columns(2)
col1.metric('Death locations shown', len(filtered_df[filtered_df['count'] != -999]))
col2.metric('Pumps in dataset', len(pumps_df))

st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=51.5134,
        longitude=-0.1365,
        zoom=15.5,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=filtered_df[filtered_df['count'] != -999],
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius='[count]',
            pickable=True,
        ),
        pdk.Layer(
            'ScatterplotLayer',
            data=pumps_df,
            get_position='[lon, lat]',
            get_color='[0, 0, 255, 160]',
            get_radius=pump_radius,
            pickable=True,
        ),
     ],
    # CHANGE 2 done by Nour: add hover tooltip
    tooltip={
        'html': '<b>Deaths:</b> {count}',
        'style': {'backgroundColor': 'white', 'color': 'black'}
    }
))

st.markdown('The red dots show the locations of deaths with a size reflecting the numbers of deaths, and the blue dots show the locations of water pumps.')

# CHANGE 3  done by Nour: optional filtered table
if st.checkbox('Show filtered data table'):
    st.dataframe(filtered_df[filtered_df['count'] != -999])

image = Image.open('Snow-cholera-map-1.jpg')

st.subheader('Original map of John Snow')
st.image(image,caption='Original map by John Snow showing the clusters of cholera cases in the London epidemic of 1854, drawn and lithographed by Charles Cheffins',use_container_width=True)

st.markdown('The source of the above map and more details on John Snow\'s work can be found here: [https://en.wikipedia.org/wiki/John_Snow](https://en.wikipedia.org/wiki/John_Snow)')

st.markdown("Developed by [Fouad Zablith](http://fouad.zablith.org). If you have any question about this simple app, you can reach me through: [@fzablith](https://twitter.com/fzablith)")
