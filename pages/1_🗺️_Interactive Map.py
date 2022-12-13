import streamlit as st
import geemap.foliumap as geemap
from datetime import date
import ee
from Algorithms.lst_psc import LandsatLSTretrieval

# ee.Initialize()
st.header('Interactive Map')

with st.sidebar:
    basemap_list = ['ROADMAP','SATELLITE','TERRAIN','Esri.WorldImagery']
    st.selectbox('Choose Basemaps', options=basemap_list, key='basemap')

    with st.expander("Search by Coordianate", expanded=True):
        with st.form("my_form"):
            st.text_input('Masukkan Latitude', value=-6.737246, key='latitude')
            st.text_input('Masukkan Longitude', value=108.550659, key='longitude')
            submit = st.form_submit_button("Submit")

def load_dataset(latitude, longitude, cloudmask):

    def mask(image):
        qa = image.select('QA_PIXEL')
        mask_cloud = qa.bitwiseAnd(1 << 3).eq(0)
        mask_shadow = qa.bitwiseAnd(1 << 4).eq(0)
        
        return image.updateMask(mask_cloud) \
                    .updateMask(mask_shadow)

    site = ee.Geometry.Point([longitude, latitude])
    geometry = site.buffer(30)

    if cloudmask:
        dataset = LandsatLSTretrieval('L8', '2013-01-01', str(date.today()), geometry) \
                  .map(mask)
    
    else:
        dataset = LandsatLSTretrieval('L8', '2013-01-01', str(date.today()), geometry)

    return dataset

with st.expander('Show Demo'):
    st.image('Data/Pictures/Demo/InteractiveMap_demo.gif', use_column_width=True)

if 'pass' not in st.session_state:
    st.session_state['pass'] = False

if submit or st.session_state['pass']:

    st.session_state['pass'] = True
    latitude = float(st.session_state.latitude)
    longitude = float(st.session_state.longitude)

    # dataset = load_dataset(latitude, longitude)
    # scene_list = dataset.aggregate_array('system:index').getInfo()

    with st.sidebar:
        with st.expander('Scene Options'):
            mask_container = st.container()
            masking = st.checkbox('Cloud Masking')
            if masking:
                st.session_state['mask'] = True
                dataset = load_dataset(latitude, longitude, True)
                scene_list = dataset.aggregate_array('system:index').getInfo()
                mask_container.selectbox('Choose Scene', options=scene_list, key='scene_id')
            
            else:
                st.session_state['mask'] = False
                dataset = load_dataset(latitude, longitude, False)
                scene_list = dataset.aggregate_array('system:index').getInfo()
                mask_container.selectbox('Choose Scene', options=scene_list, key='scene_id')

        with st.expander('Layer Options'):
            st.markdown(' ')  
            # Composite Band
            composite_container = st.container()
            composite_all = st.checkbox('All composites')
            composite_options = ['True Color', 'False Color', 'Color Infrared',
                                'Agriculture', 'Atmospheric Penetration', 'Healthly Vegetation',
                                'Land/Water', 'Natural with Atmospheric Removal', 'Shortwave Infrared',
                                'Vegetation Analysis']

            if composite_all:
                composite_container.multiselect(
                            label = 'Band Composite',
                            options = composite_options,
                            default = composite_options,
                            key = 'band_composite')

            else:
                composite_container.multiselect(
                            label = 'Band Composite',
                            options = composite_options,
                            key = 'band_composite')
            # List of bands
            bandlist_container = st.container()
            bandlist_all = st.checkbox('All bands')
            bandlist_options = ['B1','B2','B3','B4',
                                'B5','B6','B7',
                                'NDVI','NDBI','NDWI','LST'
                                ]

            if bandlist_all:
                bandlist_container.multiselect(
                            label = 'List of bands', 
                            options = bandlist_options, 
                            default = bandlist_options, 
                            key = 'band_list')

            else:
                bandlist_container.multiselect(
                            label = 'List of bands', 
                            options = bandlist_options, 
                            key = 'band_list')

    composite = st.session_state['band_composite']
    bands = []

    for item in composite:
        if item == 'True Color':
            bands.append({'True Color':['SR_B4','SR_B3','SR_B2']})
        elif item == 'False Color':
            bands.append({'False Color':['SR_B7','SR_B6','SR_B4']})
        elif item == 'ColorInfrared':
            bands.append({'Color Infrared':['SR_B5','SR_B4','SR_B3']})
        elif item == 'Agriculture':
            bands.append({'Agriculture':['SR_B6','SR_B5','SR_B2']})
        elif item == 'Atmospheric Penetration':
            bands.append({'Atmospheric Penetration':['SR_B7','SR_B6','SR_B5']})
        elif item == 'Healthly Vegetation':
            bands.append({'Healthly Vegetation':['SR_B5','SR_B6','SR_B2']})
        elif item == 'Land/Water':
            bands.append({'Land/Water':['SR_B5','SR_B6','SR_B4']})
        elif item == 'Natural with Atmospheric Removal':
            bands.append({'Natural with Atmospheric Removal':['SR_B7','SR_B5','SR_B3']})
        elif item == 'Shortwave Infrared':
            bands.append({'Shortwave Infrared':['SR_B7','SR_B5','SR_B4']})
        elif item == 'Vegetation Analysis':
            bands.append({'Vegetation Analysis':['SR_B6','SR_B5','SR_B4']})

    ratio = st.session_state['band_list']
    band_list = []
    for item in ratio:
        if item == 'B1':
            band_list.append('SR_B1')
        elif item == 'B2':
            band_list.append('SR_B2')
        elif item == 'B3':
            band_list.append('SR_B3')
        elif item == 'B4':
            band_list.append('SR_B4')
        elif item == 'B5':
            band_list.append('SR_B5')
        elif item == 'B6':
            band_list.append('SR_B6')
        elif item == 'B7':
            band_list.append('SR_B7')

        elif item == 'NDVI':
            band_list.append('NDVI')
        elif item == 'NDWI':
            band_list.append('NDBI')
        elif item == 'NDWI':
            band_list.append('NDWI')
        elif item == 'LST':
            band_list.append('LST')

    Map = geemap.Map(
        # location=[latitude, longitude],
        # zoom_start=12,
        add_google_map=False,
        plugin_Draw=False,
        search_control=False,
        plugin_LatLngPopup=True
    )

    basemap = st.session_state['basemap']
    scene = st.session_state['scene_id']

    @st.experimental_memo(show_spinner=False)
    def layer(latitude, longitude, basemap, scene, bands, cloudmask, band_list):

        data = load_dataset(latitude, longitude, cloudmask).filter(ee.Filter.eq('system:index', scene)) \
                    .first()

        popup = f'Latitude: {latitude}\nLongitude: {longitude}'
        Map.add_basemap(basemap=basemap)
        Map.add_marker(location=[latitude, longitude], tooltip=popup)

        for dict in bands:
            for key,value in dict.items():
                Map.addLayer(data, {'min':0,'max':0.3,'bands':value}, key, True)

        for item in band_list:
            if item == 'SR_B1':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B2':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B3':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B4':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B5':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B6':
                Map.addLayer(data, {'bands':item}, item, True)
            elif item == 'SR_B7':
                Map.addLayer(data, {'bands':item}, item, True)

            elif item == 'NDVI':
                vizparams = {
                    'min':-1, 
                    'max':1, 
                    'bands':item, 
                    'palette': ['blue', 'white', 'green']
                    }
                Map.addLayer(data, vizparams, item, True)
                Map.add_colorbar(vizparams, label='NDVI')

            elif item == 'NDWI':
                vizparams = {
                    'min':-1, 
                    'max':1, 
                    'bands':item
                    }
                Map.addLayer(data, vizparams, item, True)

            elif item == 'NDBI':
                vizparams = {
                    'min':-1, 
                    'max':1, 
                    'bands':item
                    }
                Map.addLayer(data, vizparams, item, True)

            elif item == 'LST':
                vizparams = {
                    'min':20, 
                    'max':40, 
                    'bands':item, 
                    'palette':['blue', 'cyan', 'green', 'yellow', 'red']
                    }
                Map.addLayer(data, vizparams, item, True)
                Map.add_colorbar(vizparams, label='LST')

        Map.centerObject(ee.Geometry.Point([longitude, latitude]), zoom=11)
        Map.to_streamlit(height=480)

    layer(

        latitude=latitude,
        longitude=longitude,
        basemap=basemap,
        scene=st.session_state.scene_id,
        bands=bands,
        cloudmask=st.session_state.mask,
        band_list=band_list

    )

else:
    Map = geemap.Map(
        add_google_map=False,
        plugin_Draw=False,
        search_control=False,
        plugin_LatLngPopup=True
        )

    Map.add_basemap(basemap=st.session_state['basemap'])

    Map.to_streamlit(height=480)



