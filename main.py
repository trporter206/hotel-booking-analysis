import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

bookings = pd.read_csv('hotel_bookings.csv')
df = bookings.copy()

# clean data

null_replacements = {'children': 0.0,
                     'country': 'unknown',
                     'company': 0,
                     'agent': 0}
df.fillna(null_replacements, inplace=True)

df['meal'].replace('Undefined', 'SC', inplace=True)

missing_guests = list(df.loc[df['adults']+df['children']+df['babies']==0].index)
df.drop(df.index[missing_guests], inplace=True)

df["hotel"] = pd.Categorical(df["hotel"])
# df["is_canceled"] = pd.Categorical(df["is_canceled"])
df["market_segment"] = pd.Categorical(df["market_segment"])
df["distribution_channel"] = pd.Categorical(df["distribution_channel"])
df["is_repeated_guest"] = pd.Categorical(df["is_repeated_guest"])
df["reserved_room_type"] = pd.Categorical(df["reserved_room_type"])
df["assigned_room_type"] = pd.Categorical(df["assigned_room_type"])
df["deposit_type"] = pd.Categorical(df["deposit_type"])
df["customer_type"] = pd.Categorical(df["customer_type"])
df["meal"] = pd.Categorical(df["meal"])
df['agent'] = df['agent'].astype(str)
df['company'] = df['company'].astype(str)
df['reservation_status_date'] = pd.to_datetime(df['reservation_status_date'])

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
months_num = ["01","02","03","04","05","06","07","08","09","10","11","12"]
df['arrival_date_month'].replace(months, months_num, inplace=True)

df['arrival_date_day_of_month'] = df['arrival_date_day_of_month'].astype(str)
df['arrival_date_day_of_month'] = df['arrival_date_day_of_month'].str.zfill(2)

df['total_guests'] = df.adults + df.children + df.babies
df['total_nights'] = df.stays_in_weekend_nights + df.stays_in_week_nights
df['arrival_date'] = df.arrival_date_year.astype(str) +'/'+ df.arrival_date_month.astype(str) +'/'+ df.arrival_date_day_of_month.astype(str)
df['arrival_date'] = pd.to_datetime(df['arrival_date'], format="%Y/%m/%d")

df['booking_date'] = df['arrival_date'] - pd.to_timedelta(df['lead_time'], unit='d')

# df.drop(columns= ['arrival_date_year', 'arrival_date_month', 'arrival_date_day_of_month'], inplace=True)

resort_data = df.loc[(df['hotel'] == 'Resort Hotel') & (df['is_canceled'] == 0)]
city_data = df.loc[(df['hotel'] == 'City Hotel') & (df['is_canceled'] == 0)]

################################################################################

# where do guests come from ----------------------------------------------------

country_data = pd.DataFrame(city_data[city_data['is_canceled']==0]['country'].value_counts())
country_data.rename(columns={'country': 'Number of Guests'}, inplace=True)

total_guests = country_data['Number of Guests'].sum()
country_data['% of guests'] = country_data['Number of Guests'] / total_guests * 100
country_data['country'] = country_data.index
country_data.drop(columns='country', inplace=True)

fig = px.pie(country_data,
             values='Number of Guests',
             names=country_data.index,
             title='Home Country of Guests by %',
             template='seaborn',)
fig.update_traces(textposition="inside", textinfo="value+percent+label")

guest_map = px.choropleth(country_data,
                          locations = country_data.index,
                          color = country_data['% of guests'],
                          hover_name = country_data.index,
                          color_continuous_scale='Viridis',
                          title="Home country of guests")

# fig.show()
# guest_map.show()

# how much do guests pay per night/person --------------------------------------

df['adr_pp'] = df['adr'] / df['total_guests']
df_guests = df.loc[df['is_canceled'] == 0]
room_prices = df[['hotel', 'reserved_room_type', 'adr_pp']].sort_values('reserved_room_type')

plt.figure(figsize=(8,5))
sns.set()
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.boxplot(x='reserved_room_type',
            y='adr_pp',
            hue='hotel',
            data=room_prices,
            palette=['#7186a8', '#ffad14'],
            hue_order=['City Hotel', 'Resort Hotel'],
            fliersize=0)
plt.title("Price of room types per night and person", fontsize=16)
plt.xlabel("Room type", fontsize=16)
plt.ylabel("Price [EUR]", fontsize=16)
plt.legend(loc="upper right")
plt.ylim(0, 160)

# how does price per night change over the year --------------------------------
room_prices = df[['hotel', 'arrival_date_month', 'adr_pp']].sort_values('arrival_date_month')
months= ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
room_prices.replace(room_prices['arrival_date_month'].unique(), months, inplace=True)
plt.figure(figsize=(8,5))
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.lineplot(x='arrival_date_month',
             y='adr_pp',
             hue='hotel',
             data=room_prices,
             palette=['#7186a8', '#ffad14'],
             hue_order = ["City Hotel", "Resort Hotel"],
             ci="sd",
             size="hotel",
             sizes=(2.5, 2.5))
plt.title("Room price per night and person over the year", fontsize=16)
plt.xlabel('Months', fontsize=16)
plt.xticks(rotation=45)
plt.ylabel("Price [EUR]", fontsize=16)
#
# # what are the busiest months --------------------------------------------------
#
city_guests = city_data.groupby('arrival_date_month')['hotel'].count()
resort_guests = resort_data.groupby('arrival_date_month')['hotel'].count()

city_guests_data = pd.DataFrame({'month': list(city_guests.index),
                                 'hotel': 'City Hotel',
                                 'guests': list(city_guests.values)})
resort_guests_data = pd.DataFrame({'month': list(resort_guests.index),
                                   'hotel': 'Resort Hotel',
                                   'guests': list(resort_guests.values)})
full_guests = pd.concat([resort_guests_data, city_guests_data], ignore_index=True)
full_guests['month'].replace(months_num, months, inplace=True)

full_guests.loc[(full_guests["month"] == "July") | (full_guests["month"] == "August"), "guests"] /= 3
full_guests.loc[~((full_guests["month"] == "July") | (full_guests["month"] == "August")), "guests"] /= 2

plt.figure(figsize=(8,5))
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.lineplot(x='month',
             y='guests',
             data=full_guests,
             hue='hotel',
             palette=['#7186a8', '#ffad14'],
             hue_order=["City Hotel", "Resort Hotel"],
             size="hotel",
             sizes=(2.5, 2.5),
             sort=False)
plt.title('Guests per Month', fontsize=16)
plt.xlabel('Month', fontsize=16)
plt.xticks(rotation=45)
plt.ylabel('Total guests', fontsize=16)
#
# # how long do people stay ------------------------------------------------------
#
city_nights = city_data['total_nights'].value_counts()
resort_nights = resort_data['total_nights'].value_counts()

city_nights_data = pd.DataFrame({'total nights': list(city_nights.index),
                                 'hotel': 'City Hotel',
                                 'count': list(city_nights.values)})
resort_nights_data = pd.DataFrame({'total nights': list(resort_nights.index),
                                 'hotel': 'Resort Hotel',
                                 'count': list(resort_nights.values)})
full_nights_data = pd.concat([resort_nights_data, city_nights_data], ignore_index=True)
full_nights_data['count'] = (full_nights_data['count']/full_nights_data['count'].sum()) * 100

plt.figure(figsize=(8,5))
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.barplot(x='total nights',
            y='count',
            data=full_nights_data,
            hue='hotel',
            palette=['#7186a8', '#ffad14'],
            hue_order=["City Hotel", "Resort Hotel"])
plt.title("Length of stay", fontsize=16)
plt.xlabel("Number of nights", fontsize=16)
plt.ylabel("Guests [%]", fontsize=16)
plt.legend(loc="upper right")
plt.xlim(0,15)
#
# # bookings by market segment ---------------------------------------------------
#
city_segments = city_data['market_segment'].value_counts()
resort_segments = resort_data['market_segment'].value_counts()

city_segments_data = pd.DataFrame({'market segment': list(city_segments.index),
                                   'count': list(city_segments.values)})
resort_segments_data = pd.DataFrame({'market segment': list(resort_segments.index),
                                     'count': list(resort_segments.values)})

city_labels = city_segments_data['market segment']
city_values = city_segments_data['count']
resort_labels = resort_segments_data['market segment']
resort_values = resort_segments_data['count']

city_fig = go.Figure(data=[go.Pie(labels=city_labels, values=city_values)])
resort_fig = go.Figure(data=[go.Pie(labels=resort_labels, values=resort_values)])
# city_fig.show()
# resort_fig.show()
#
# # ADR by market segment and room tpye ------------------------------------------
plt.figure(figsize=(8,5))
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.barplot(x='market_segment',
            y='adr_pp',
            data=df,
            hue='reserved_room_type',
            palette='bright',
            ci="sd",
            errwidth=1,
            capsize=0.1)

plt.title("ADR by market segment and room type", fontsize=16)
plt.xlabel("Market segment", fontsize=16)
plt.xticks(rotation=45)
plt.ylabel("ADR per person [EUR]", fontsize=16)
plt.legend(loc="upper right")
#
# # look into airline data -------------------------------------------------------
#
aviation_data = df.loc[df['market_segment'] == 'Aviation']
non_aviation_data = df.loc[df['market_segment'] != 'Aviation']

# print aviation_data[['lead_time', 'adr_pp']].describe()
# print non_aviation_data[['lead_time', 'adr_pp']].describe()
#
# # monthly cancellations --------------------------------------------------------
#
res_monthly_booking = df.loc[df['hotel'] == 'Resort Hotel']['arrival_date_month'].value_counts().sort_index()
city_monthly_booking = df.loc[df['hotel'] == 'City Hotel']['arrival_date_month'].value_counts().sort_index()

res_monthly_cancels = df.loc[df['hotel'] == 'Resort Hotel'].groupby('arrival_date_month')['is_canceled'].sum()
city_monthly_cancels = df.loc[df['hotel'] == 'City Hotel'].groupby('arrival_date_month')['is_canceled'].sum()

res_cancel_data = pd.DataFrame({'month': list(res_monthly_booking.index),
                                'bookings': list(res_monthly_booking.values),
                                'cancellations': list(res_monthly_cancels.values),
                                'hotel': 'Resort Hotel'})
city_cancel_data = pd.DataFrame({'month': list(city_monthly_booking.index),
                                 'bookings': list(city_monthly_booking.values),
                                 'cancellations': list(city_monthly_cancels.values),
                                 'hotel': 'City Hotel'})
full_cancel_data = pd.concat([res_cancel_data, city_cancel_data], ignore_index=True)
# full_cancel_data['month'].replace(months_num, months, inplace=True)

full_cancel_data['cancellations'] = (full_cancel_data['cancellations']/full_cancel_data['bookings']) * 100

plt.figure(figsize=(8,5))
sns.set_style(rc={'grid.color': '.8',
                  'axes.facecolor': 'white',})
sns.lineplot(x='month',
            y='cancellations',
            data=full_cancel_data,
            hue='hotel',
            palette=['#7186a8', '#ffad14'],
            hue_order = ["City Hotel", "Resort Hotel"])
plt.title('Bookings and Cancellations per month')
plt.ylabel('Cancellations [%]', fontsize=16)
plt.xlabel('Month', fontsize=16)
#
# # cancel correlations ----------------------------------------------------------
#
cancel_corr = df.corr()['is_canceled']
# print cancel_corr.abs().sort_values(ascending=False)[1:]
# print df.groupby('is_canceled')['reservation_status'].value_counts()

num_features = ["lead_time","arrival_date_week_number","arrival_date_day_of_month",
                "stays_in_weekend_nights","stays_in_week_nights","adults","children",
                "babies","is_repeated_guest", "previous_cancellations",
                "previous_bookings_not_canceled","agent","company",
                "required_car_parking_spaces", "total_of_special_requests", "adr"]

cat_features = ["hotel","arrival_date_month","meal","market_segment",
                "distribution_channel","reserved_room_type","deposit_type","customer_type"]

features = num_features+cat_features
x=df.drop(['is_canceled'], axis=1)[features]
y=df['is_canceled']

plt.show()
