import pandas as pd
from bokeh.plotting import figure, output_file, show
from bokeh.models.widgets import Slider,Select, CheckboxGroup 
from bokeh.models import ColumnDataSource,HoverTool, Spacer
from bokeh.layouts import layout, widgetbox
import numpy as np
from bokeh.io import curdoc


tv_data = pd.read_csv("data/tv_data.csv")
tv_data = tv_data.drop(['Unnamed: 0'], axis=1)

tv_data["color"] = "grey"
tv_data["alpha"] = 0.9

tv_data["brand"] = pd.np.where(tv_data.TV_name.str.contains("Samsung"), "Samsung",
                   pd.np.where(tv_data.TV_name.str.contains("LG"), "LG",
                   pd.np.where(tv_data.TV_name.str.contains("Sony"), "Sony",
                   pd.np.where(tv_data.TV_name.str.contains("Philips"), "Philips", 
                   pd.np.where(tv_data.TV_name.str.contains("Thomson"), "Thomson","0")))))

axis_map = {
    "Price": "Price",
    "Length of the diagonal": "diagonal",
    "Number of HDMI ports": "hdmi_n",
    "Number of USB ports": "usb_n",
    "3D TV": "3D_Tv",
    "Volume": "volume",
    "Pixels": "pixels",
    "Energy consumption (kWh/year)": "energy_cons",
    "Weight": "weight"
}

hd_map = {
    "Ultra HD (4K)": "ultra",
    "Full HD": "full",
    "All": "all"
}
yes_no_map = {
    "Yes": 1,
    "No": 0
}


#########################################################################################################
# Create Input controls
#########################################################################################################

# Sliders and Selects
min_price_   = Slider(title="Minimum price", value=0, start=0, end=3000000, step=10000)
max_price_   = Slider(title="Maximum price", value=3000000, start=0, end=3000000, step=10000)
diag_min_    = Slider(title="Minimum length of diagonal", value=0, start=0, end=218, step=10)
vol_min_     = Slider(title="Minimum volume", value=0, start=0, end=80, step=5)
pix_min_     = Slider(title="Minimum number of pixels", value=0, start=0, end=8200000, step=10000)
energy_max_  = Slider(title="Max energy consumed (kwh/year)", value=420, start=0, end=420, step=20)
weight_max_  = Slider(title="Max Weight (kg)", value=100, start=0, end=100, step=5)
hdmi_min_    = Slider(title="Minimum number of HDMI ports", value=0, start=0, end=4, step=1)
usb_min_     = Slider(title="Minimum number of USB ports", value=0, start=0, end=3, step=1)
hd_          = Select(title="Type of HD", options=sorted(hd_map.keys()), value="All")
tv_3d_       = Select(title="3D TV", options=sorted(yes_no_map.keys()), value="No")
x_axis       = Select(title="X Axis", options=sorted(axis_map.keys()), value="Length of the diagonal")
y_axis       = Select(title="Y Axis", options=sorted(axis_map.keys()), value="Price")

# Create Checkbox controls
checkbox_group = CheckboxGroup(labels=["Samsung", "LG", "Philips","Thomson","Sony"], active=[],width= 120)


#########################################################################################################
# Define functions
#########################################################################################################

# Updata data if something change
def get_data():
    hd_e = hd_map[hd_.value]
    full_h_e = hd_map[hd_.value]
    tv_3d_e = yes_no_map[tv_3d_.value]
    
    # Filter sliders
    selected_tv = tv_data[
        (tv_data.Price        >= min_price_.value)  &
        (tv_data.Price        <= max_price_.value)  &
        (tv_data.diagonal     >= diag_min_.value)   &
        (tv_data.hdmi_n       >= hdmi_min_.value)   &
        (tv_data.usb_n        >= usb_min_.value)    &       
        (tv_data.volume       >= vol_min_.value)    &
        (tv_data.pixels       >= pix_min_.value)    &
        (tv_data.energy_cons  <= energy_max_.value) &
        (tv_data.weight       <= weight_max_.value) 
    ]

    # Filters selelct
    if (hd_e == "full"):
        selected_tv = selected_tv[selected_tv.Full_HD == 1]
    if (hd_e == "ultra"):
        selected_tv = selected_tv[selected_tv.Ultra_HD == 1]
    
    # Brand checkbox
    carriers_to_plot = [checkbox_group.labels[i] for i in checkbox_group.active]
    
    if len(carriers_to_plot) != 0: 
        selected_tv["color"] = np.where(selected_tv["brand"].isin(carriers_to_plot), '#ffe400', 'grey')
        selected_tv["alpha"] = np.where(selected_tv["brand"].isin(carriers_to_plot), 0.9, 0.5)
    
    # 3D tv
    if (tv_3d_e == 1):
         selected_tv = selected_tv[selected_tv['3D_Tv'] == 1]
            
    return(selected_tv)

# Get data to boxplot
def box_data(score_,group_):
    df = pd.DataFrame(dict(score=score_, group=group_))
    df1 = pd.DataFrame()
    
    groups = df.groupby('group')
    df1['qmin'] = groups.quantile(q=0.00).score
    df1['qmax'] = groups.quantile(q=1.00).score
    df1['q1']   = groups.quantile(q=0.25).score
    df1['q2']   = groups.quantile(q=0.5).score
    df1['q3']   = groups.quantile(q=0.75).score
    df1['iqr']  = df1['q3'] - df1['q1']
    df1['upper'] = df1['q3'] + 1.5*df1['iqr']
    df1['lower'] = df1['q1'] - 1.5*df1['iqr']
    df1['upper_score'] = [min([x,y]) for (x,y) in zip(df1['qmax'],df1['upper'])]
    df1['lower_score'] = [max([x,y]) for (x,y) in zip(df1['qmin'],df1['lower'])]
    df1['group'] = df1.index
    
    out = pd.DataFrame()
    for c in list(df.group.unique()): 
        out_f = df[df.group == c]
        out_f = out_f[(out_f.score > float(df1[df1.index == c]['upper'])) |
                                  (out_f.score < float(df1[df1.index == c]['lower']))
                                 ]    
        out = out.append(out_f,ignore_index=True)
    
    return{'main':df1,'outlier':out}


# Update graph
def update():
    df = get_data()
    
    # Scatter
    x_name = axis_map[x_axis.value]
    y_name = axis_map[y_axis.value]

    p.xaxis.axis_label = x_axis.value
    p.yaxis.axis_label = y_axis.value
    
    p.title.text = "%d TVs selected" % len(df)

    source_tv.data = dict(
        x=df[x_name],
        y=df[y_name],
        color=df["color"],
        alpha=df["alpha"],
        tv_name=df['TV_name'],
        price=df['Price']
    )
    
    # Histagram
    price_hist, edges = np.histogram(source_tv.data['price'], 
                          bins = int(len(source_tv.data['price'])/8))
    
    price_rangs.data = dict(
                       price_hist_ = price_hist, 
                       left = edges[:-1], 
                       right = edges[1:])
    
    # Boxplot
    data_b = box_data(score_ = df['Price'], group_ = df['brand'])
    

    main_data.data = dict(
                          upper =  data_b['main']['upper'],
                          lower =  data_b['main']['lower'],
                          q1 =  data_b['main']['q1'],
                          q2 =  data_b['main']['q2'],
                          q3 =  data_b['main']['q3'],
                          group = data_b['main']['group'])

    outlier_data.data = dict(
                             group = data_b['outlier']['group'],
                             score = data_b['outlier']['score'])



#########################################################################################################
# Plots
#########################################################################################################


#### Scatter Plot ####
# Create Column Data Source that will be used by the plot
source_tv = ColumnDataSource(data=dict(x=tv_data["diagonal"], y=tv_data["Price"], color=tv_data["color"], 
                                       alpha=tv_data["alpha"],tv_name=tv_data["TV_name"],price=tv_data["Price"]))

# Create scatter plot
p = figure(plot_height=600, plot_width=600, title="", toolbar_location=None)
p.circle(x= 'x', y= 'y', source = source_tv, size=7, fill_alpha='alpha', color = 'color')

# Manage Hovertool
hover = HoverTool()
hover.tooltips = [
    ("Name", "@tv_name"),
    ("Price", "@price")
]
p.tools.append(hover)



#### Histogram ####
price_hist, edges = np.histogram(source_tv.data['price'], 
                               bins = int(len(source_tv.data['price'])/8))
# Put the information in a dataframe
price_rangs =  ColumnDataSource(data=dict(price_hist_ = price_hist, 
                       left = edges[:-1], 
                       right = edges[1:]))

h = figure(plot_height = 300, plot_width = 600, 
           title = 'Histogram TV prices',
           x_axis_label = 'Price', 
           y_axis_label = 'Number of Tvs',
           toolbar_location=None)

# add a line renderer with legend and line thickness
h.quad(source = price_rangs,
       bottom=0, top='price_hist_', 
       left='left', 
       right='right', 
       fill_color='#ffe400', 
       line_color='gray',
       alpha =0.9)


#### Boxplot ####

data_b = box_data(score_ = tv_data['Price'], group_ = tv_data['brand'])

# generate some synthetic time series for six different categories
main_data = ColumnDataSource(data = dict(
                          upper =  data_b['main']['upper'],
                          lower =  data_b['main']['lower'],
                          q1 =  data_b['main']['q1'],
                          q2 =  data_b['main']['q2'],
                          q3 =  data_b['main']['q3'],
                          group = data_b['main']['group']))

outlier_data = ColumnDataSource(data = dict(
                             group = data_b['outlier']['group'],
                             score = data_b['outlier']['score']))

b = figure(plot_height=600, plot_width=600, tools="save", background_fill_color="white", title="", 
             x_range = tv_data["brand"].unique(),
           toolbar_location=None)

# stems
b.segment('group','upper', 'group', 'q3', line_color="black",source = main_data )
b.segment('group','lower', 'group', 'q1', line_color="black",source = main_data)

# boxes
b.vbar('group', 0.7, 'q2', 'q3', fill_color="#ffe400", line_color="black",source = main_data)
b.vbar('group', 0.7, 'q1', 'q2', fill_color="#999999", line_color="black",source = main_data)

# whiskers (almost-0 height rects simpler than segments)
b.rect('group', 'lower', 0.2, 0.01, line_color="black",source = main_data)
b.rect('group', 'upper', 0.2, 0.01, line_color="black",source = main_data)

# outliers
b.circle('group', 'score', size=6, color="#ffbf00", fill_alpha=0.5,
         source = outlier_data)

b.xgrid.grid_line_color = None
b.ygrid.grid_line_color = "#e1dcdc"
b.xaxis.major_label_text_font_size="12pt"



        
#### Widgets ####
controls = [min_price_, max_price_, diag_min_,vol_min_,pix_min_ ,energy_max_,weight_max_,hdmi_min_, usb_min_,
            hd_ ,tv_3d_, 
            x_axis, y_axis]

for control in controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example
inputs = widgetbox(*controls, sizing_mode=sizing_mode)

checkbox_group.on_change('active', lambda attr, old, new: update())

# Layout
l = layout([
    [inputs, p, checkbox_group, b],
    [Spacer(width=300, height=300), h, Spacer(width=50, height=300),Spacer(width=600, height=300)]
], sizing_mode=sizing_mode)

update()  # initial load of the data

curdoc().add_root(l)