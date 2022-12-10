from statistics import geometric_mean
import streamlit as st
import pandas as pd
import ee
from Algorithms.lst_psc import LandsatLSTretrieval
from datetime import date
import geemap.foliumap as geemap
import altair as alt

st.set_page_config(
    page_title='Land Surface Temperature'
)

st.header('🌡️ Land Surface Temperature')
st.expander('Show Demo').write('Lorem Ipsum')

def input_data():
  
    st.selectbox('Select the City', options=['Cirebon','Kab.Cirebon'], key='geometry')

    if st.session_state.geometry == 'Cirebon':
        geometry = geemap.shp_to_geojson('Data/Kota Cirebon/KotaCirebon.shp')
        center = [-6.737246, 108.550659]
        zoom_start = 12

    elif st.session_state.geometry == 'Kab.Cirebon':
        geometry = geemap.shp_to_geojson('Data/Kab.Cirebon/Adm_Kab_Crb.shp')
        center = [-6.80000000, 108.56667000]
        zoom_start = 10

    with st.expander('Determine of Sample Point', expanded=True):

        with st.form('Form-1'):
            st.text_input('Latitude', value=-6.737246, key='latitude')
            st.text_input('Longitude', value=108.550659, key='longitude')
            submit = st.form_submit_button("Submit")

        global latitude, longitude, site, site_buffer

        latitude = float(st.session_state['latitude'])
        longitude = float(st.session_state['longitude'])
        site = ee.Geometry.Point([longitude, latitude])
        site_buffer = site.buffer(30)

        @st.experimental_memo(show_spinner=False)
        def add_map(geometry,latitude,longitude):
            geo = geemap.Map(
                center=center,
                zoom_start=zoom_start,
                add_google_map=False,
                tiles="cartodbpositron",
                plugin_Draw=False,
                search_control=False,
                plugin_Fullscreen=False,
                plugin_LatLngPopup=True
                )
            geo.add_geojson(geometry, layer_name='geometry', info_mode=False)

            popup = f'Latitude: {latitude}\nLongitude: {longitude}'
            geo.add_marker(location=[latitude, longitude], tooltip=popup)
            geo.to_streamlit(height=480)

        add_map(
            geometry,
            latitude,
            longitude
            )

        st.button(
            label='Discover the Land Surface Temperature data!',
            key='button'
            )

def result(latitude, longitude, site, site_buffer):
    if st.session_state['button']:
        with st.spinner("Please Wait..."):

            dataset = LandsatLSTretrieval('L8', '2013-01-01', str(date.today()), site)

            # Load dataframe
            def load_dataframe():

                def properties(image):
                    date = ee.Date(image.get('system:time_start'))
                    ndvi = image.select('NDVI')
                    fvc = image.select('FVC')
                    em = image.select('Emissivity')
                    awv = image.select('AWVhour')
                    lst = image.select('LST')
                    return ee.Feature(site, {
                        'Longitude':ee.Number(site.coordinates().get(0)),
                        'Latitude':ee.Number(site.coordinates().get(1)),
                        'Id': ee.String(image.get('system:index')),
                        'Date':ee.Number(date.format('YYYY-MM-dd')),
                        'Time':ee.Number(date.format('k:m:s')),
                        'NDVI':ee.Number(ndvi.reduceRegion(ee.Reducer.mean(),site_buffer,30).get('NDVI')),
                        'FVC':ee.Number(fvc.reduceRegion(ee.Reducer.mean(),site_buffer,30).get('FVC')),
                        'Emissivity':ee.Number(em.reduceRegion(ee.Reducer.mean(),site_buffer,30).get('Emissivity')),
                        'WaterVapor':ee.Number(awv.reduceRegion(ee.Reducer.mean(),site_buffer,30).get('AWVhour')),
                        'LST': ee.Number(lst.reduceRegion(ee.Reducer.mean(),site_buffer,30).get('LST'))
                    })

                def mask(image):
                    qa = image.select('QA_PIXEL')
                    mask_cloud = qa.bitwiseAnd(1 << 3).eq(0)
                    mask_shadow = qa.bitwiseAnd(1 << 4).eq(0)

                    return image.updateMask(mask_cloud) \
                                .updateMask(mask_shadow)

                fc = ee.FeatureCollection(dataset.map(mask) \
                                                    .map(properties)
                    )
                    
                fc_to_df = geemap.ee_to_pandas(fc)
                df = fc_to_df.loc[:, ['Id','Latitude','Longitude','Date','Time','NDVI','FVC','Emissivity','WaterVapor','LST']]

                return df
        
            with st.expander('Show Gift Animation', expanded=True):

                LSTParams = {'min': 17 , 'max': 45, 'palette': ['blue', 'yellow','red']}

                if st.session_state.geometry == 'Cirebon':
                    roi = geemap.shp_to_ee('Data/Kota Cirebon/KotaCirebon.shp')

                elif st.session_state.geometry == 'Kab.Cirebon':
                    roi = geemap.shp_to_ee('Data/Kab.Cirebon/Adm_Kab_Crb.shp')

                def reducebyYear(year):

                    def clip(image):
                        return image.clip(roi)

                    def mask(image):
                        qa = image.select('QA_PIXEL')
                        mask_cloud = qa.bitwiseAnd(1 << 3).eq(0)
                        mask_shadow = qa.bitwiseAnd(1 << 4).eq(0)

                        return image.updateMask(mask_cloud) \
                                    .updateMask(mask_shadow)

                    start_date = ee.Date.fromYMD(year, 1, 1)
                    end_date = start_date.advance(1, 'year')

                    filtered = LandsatLSTretrieval('L8', start_date, end_date, site).map(mask) \
                                                                                    .select('LST') \
                                                                                    .map(clip) \
                                                                                    .median()

                    return filtered

                # Membuat gif lst tahunan
                years = ee.List.sequence(2013,2022)
                reduce_yearly = ee.ImageCollection(years.map(reducebyYear))
                videoArgs = {
                    'dimensions': 450,
                    'region': roi,
                    'framesPerSecond': 2,
                    'crs': 'EPSG:3857',
                    'min': 20,
                    'max': 40,
                    'palette': ['blue', 'cyan', 'green', 'yellow', 'red']
                }
                geemap.download_ee_video(reduce_yearly, videoArgs, 'Data/Pictures/lst.gif')

                # Menambahkan text tahun pada gambar
                text = list(range(2013,2023))               
                geemap.add_text_to_gif(
                    'Data/Pictures/lst.gif',
                    'Data/Pictures/lst.gif',
                    xy=('80%', '3%'),
                    text_sequence=text,
                    font_size=20,
                    font_color='#ffffff',
                    duration=500,
                    add_progress_bar=False
                ) 

                # Menambahkan colorbar pada gambar
                colorbar_v = geemap.create_colorbar(
                    width=250,
                    height=40,
                    palette=['blue', 'cyan', 'green', 'yellow', 'red'],
                    vertical=True,
                    add_labels=True,
                    font_size=15,
                    labels=[20, 40],
                    add_outline=False,
                    out_file='Data/Pictures/colorbar/colorbar.png',
                    font_color='white'
                )

                geemap.add_image_to_gif(
                    in_gif='Data/Pictures/lst.gif',
                    out_gif='Data/Pictures/lst.gif',
                    in_image='Data/Pictures/colorbar/colorbar.png',
                    xy=('80%', '65%'),
                    image_size=(150, 150)
                )

                cols = st.columns(3)
                cols[1].image('Data/Pictures/lst.gif', use_column_width='auto')
 
            with st.expander('Show LST Images by Yearly', expanded=True):

                geemap.gif_to_png('Data/Pictures/lst.gif', 'Data/Pictures/YearlyLST/')

                c1,c2,c3,c4 = st.columns([1,1,1,1])
                # Row 1
                c1.image('Data/Pictures/YearlyLST/1.png', caption='median LST 2013', use_column_width=True)
                c2.image('Data/Pictures/YearlyLST/2.png', caption='median LST 2014', use_column_width=True)
                c3.image('Data/Pictures/YearlyLST/3.png', caption='median LST 2015', use_column_width=True)
                c4.image('Data/Pictures/YearlyLST/4.png', caption='median LST 2016', use_column_width=True)
                # Row 2               
                c1.image('Data/Pictures/YearlyLST/5.png', caption='median LST 2017', use_column_width=True)
                c2.image('Data/Pictures/YearlyLST/6.png', caption='median LST 2018', use_column_width=True)
                c3.image('Data/Pictures/YearlyLST/7.png', caption='median LST 2019', use_column_width=True)
                c4.image('Data/Pictures/YearlyLST/8.png', caption='median LST 2020', use_column_width=True)
                # Row 3
                c1.image('Data/Pictures/YearlyLST/9.png', caption='median LST 2021', use_column_width=True)
                c2.image('Data/Pictures/YearlyLST/10.png', caption='median LST 2022', use_column_width=True)


            with st.expander('Show Data', expanded=True):
                df = load_dataframe()
                df = df.dropna()
                df['delta'] = df.LST.diff().fillna(0)
                df['Date'] = df['Date'].astype('datetime64')
                df[['NDVI','FVC','Emissivity','WaterVapor','LST']] = df[['NDVI','FVC','Emissivity','WaterVapor','LST']].round(3)
                df['Year'] = pd.DatetimeIndex(df['Date']).year
                df['Month'] = pd.DatetimeIndex(df['Date']).month
                df['Quarter'] = pd.DatetimeIndex(df['Date']).quarter
                st.dataframe(df)

                @st.cache
                def convert_df(df):
                    # IMPORTANT: Cache the conversion to prevent computation on every rerun
                    return df.to_csv().encode('utf-8')

                csv = convert_df(df)

                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='Data_LST.csv',
                    mime='text/csv',
                )

            with st.expander('Show Chart', expanded=True):

                st.subheader('Line Chart')

                T1,T2,T3,T4,T5 = st.tabs(['All','LOESS','By Year','By Quarter','By Month'])

                with T1:
                    # Create a selection that chooses the nearest point & selects based on x-value
                    hover = alt.selection_single(
                        fields=['Date'],
                        nearest=True,
                        on="mouseover",
                        empty="none",
                    )

                    lines = alt.Chart(df).mark_line(point='transparent').encode(
                        alt.X('Date'),
                        y='LST'
                    )

                    # Draw points on the line, highlight based on selection, color based on delta
                    points = (
                        lines.transform_filter(hover)
                        .mark_circle(size=65)
                        .encode(color=alt.Color("color:N", scale=None))
                    ).transform_calculate(color='datum.delta < 0 ? "red" : "green"')

                    # Draw an invisible rule at the location of the selection
                    tooltips = (
                        alt.Chart(df)
                        .mark_rule(opacity=0)
                        .encode(
                            x='Date',
                            y='LST',
                            tooltip=['Date', 'LST', "delta"],
                        )
                        .add_selection(hover)
                    )

                    line_chart = alt.layer(lines, points, tooltips)
                    st.altair_chart(line_chart, use_container_width=True)

                with T2:
                    chart = alt.Chart(df).mark_point().encode(
                        x='Date:T',
                        y='LST:Q'
                    )
                    chart_loess = chart + chart.transform_loess('Date', 'LST').mark_line()
                    st.altair_chart(chart_loess, use_container_width=True)

                with T3:
                    byYear = alt.Chart(df).mark_line(point=True).encode(
                        alt.X('year(Date):T'),
                        alt.Y('mean(LST):Q'),
                        tooltip=[
                            alt.Tooltip('Date', timeUnit='year'),
                            alt.Tooltip('LST', aggregate='mean')
                        ]
                    )
                    st.altair_chart(byYear, use_container_width=True)
                
                with T4:
                    byQuarter = alt.Chart(df).mark_line(point=True).encode(
                        alt.X('quarter(Date):T'),
                        alt.Y('mean(LST):Q'),
                        tooltip=[
                            alt.Tooltip('Date', timeUnit='quarter'),
                            alt.Tooltip('LST', aggregate='mean')
                        ]
                    )
                    st.altair_chart(byQuarter, use_container_width=True)

                with T5:
                    byMonth = alt.Chart(df).mark_line(point=True).encode(
                        alt.X('month(Date):T'),
                        alt.Y('mean(LST):Q'),
                        tooltip=[
                            alt.Tooltip('Date', timeUnit='month'),
                            alt.Tooltip('LST', aggregate='mean')
                        ]
                    )
                    st.altair_chart(byMonth, use_container_width=True)

                st.subheader('Histogram')
                histogram = alt.Chart(df).mark_bar().encode(
                    alt.X('LST', bin=True),
                    y='count()'
                )
                st.altair_chart(histogram, use_container_width=True)

                st.subheader('Boxplot')
                boxplot = alt.Chart(df).mark_boxplot().encode(
                    alt.X('Year:O', axis=alt.Axis(labelAngle=0)),
                    alt.Y('LST:Q')
                ).properties(width=400
                )
                st.altair_chart(boxplot, use_container_width=True)

                st.subheader('Heatplot')
                heatplot = alt.Chart(df).mark_rect().encode(
                    alt.X('Month:O', axis=alt.Axis(labelAngle=0)),
                    alt.Y('Year:O'),
                    alt.Color('LST:Q', aggregate='mean', scale=alt.Scale(scheme='redyellowblue', reverse=True), title='Land Surface Temperature, °C'),
                    tooltip = [
                    alt.Tooltip('LST:Q', aggregate='mean'),
                    alt.Tooltip('Year'),
                    alt.Tooltip('Month')
                        
                    ]
                ).properties(height=400)
                st.altair_chart(heatplot, use_container_width=True)

input_data()
result(
    latitude=latitude,
    longitude=longitude,
    site=site,
    site_buffer=site_buffer
)



