import dash
import datetime
from plotly import graph_objects as go
from plotly.subplots import make_subplots




def figure_base(df, value1, checked):
    hover_text = []
    for index, row in df.iterrows ():
        hover_text.append (('<b>{city}</b><br><br>' +
                            'Time interval: {date}<br><br>' + 'Magnitude: {magn}<br><br>').format (
            city=row['City'],
            date=row['date'],
            magn=row['magnitude']
        ))
    df.loc[:,'text'] = hover_text

    df_city = df[(df['City'] == value1)]
    df_city = df_city.sort_values('date_and_time')

    print('bu yine bos mu', df_city[['date_and_time','magnitude']])




    fig = make_subplots (specs=[[{ "secondary_y": False }]])


    fig.add_trace (  # Add the second chart (line chart) to the figure
        go.Scatter (
            x=df_city['date_and_time'],
            y=df_city['magnitude'],
            mode='lines',
            name="Magnitude",
            text=df_city['text'],
            hoverinfo='text',  # Pass the 'text' column to the hoverinfo parameter to customize the tooltip
            line=dict (color='firebrick', width=3)  # Specify the color of the line
        ))
    if checked :
        paper_bgcolor = '#1a1b1e'

    else : paper_bgcolor ='white'
    print(checked)
    print(paper_bgcolor)

    fig.update_layout ( plot_bgcolor= '#56575E',paper_bgcolor=paper_bgcolor,modebar_bgcolor='#CCD0E0',
                       hoverlabel_bgcolor='#DAEEED',  # Change the background color of the tooltip to light gray
                       title_text="Earthquake Analysis of Turkey's Cities",  # Add a chart title
                       title_font_family="Times New Roman",
                       title_font_size=20,
                       title_font_color="white",  # Specify font color of the title
                       title_x=0.5,  # Specify the title position
                       xaxis=dict (
                           color="#E90",
                           showgrid=True, gridwidth=1, gridcolor='#686A73',
                           tickfont_size=10,
                           tickangle=270,
                           #showgrid=True,
                           #zeroline=True,
                           #showline=True,
                           #showticklabels=True,
                           dtick="M1",  # Change the x-axis ticks to be monthly
                           tickformat="%b\n%Y"
                       ),
                       yaxis=dict (color="#E90",showgrid=True, gridwidth=1, gridcolor='#686A73'),
                       legend=dict (orientation='h', xanchor="center", x=0.72, y=1),  # Adjust legend position
                       yaxis_title='Magnitude',
                      )

    fig.update_xaxes (

            rangeslider_visible=True,
            rangeselector=dict (
                buttons=list ([
                    dict (count=1, label="1m", step="month", stepmode="backward"),
                    dict (count=6, label="6m", step="month", stepmode="backward"),
                    dict (count=1, label="YTD", step="year", stepmode="todate"),
                    dict (count=1, label="1y", step="year", stepmode="backward"),
                    dict (step="all")
                ]))
        )

    return fig
