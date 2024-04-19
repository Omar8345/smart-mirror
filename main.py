# Imports.
from io import BytesIO
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import requests
import geocoder
import time
import json
from gnews import GNews
from decouple import config
import pycountry
import threading
import logging

logging.getLogger("geocoder").setLevel(logging.CRITICAL) # Disable geocoder logging

# The SmartMirror class for the main application.
class SmartMirror(tk.Tk):
    def __init__(self) -> None:
        """
        Initialize the Smart Mirror application
        """
        
        tk.Tk.__init__(self)

        self.debug = config("DEBUG", default=False, cast=bool)
        self.name = config("USERNAME", default="User", cast=str) + "!"

        self.attributes("-fullscreen", True)
        self.configure(background="black")
        self.wm_attributes("-alpha", 0.9)  # Adjust transparency for a modern look
        self.wm_attributes("-topmost", True)
        self.title("Smart Mirror")
        self.time = ""
        self.time_seconds = ""
        self.date = ""
        self.weather = ""
        self.weather_icon_url = ""
        self.latitude = geocoder.ip("me").latlng[0]
        self.longitude = geocoder.ip("me").latlng[1]
        self.city = geocoder.ip("me").city
        self.country = geocoder.ip("me").country
        self.news = ""
        self.create_widgets()
        self.update_clock()

        # Start separate threads for weather and news updates
        threading.Thread(target=self.update_weather).start()
        threading.Thread(target=self.update_news).start()

    def create_widgets(self) -> None:
        """
        Create the widgets for the Smart Mirror
        """

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        now = time.localtime()
        current_hour = int(time.strftime("%H", now))

        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        self.greeting_label = tk.Label(
            self.canvas, font=("Futura", 55), fg="white", bg="black"
        )
        self.greeting_label.pack(side="top", anchor="nw", padx=50, pady=50)
        self.greeting_label.config(text=f"{greeting}, {self.name}")

        time_label_font = font.Font(family="Futura", size=60, weight="bold")
        self.time_label = tk.Label(
            self.canvas, font=time_label_font, fg="white", bg="black"
        )
        self.time_label.pack(side="top", anchor="nw", padx=50)

        seconds_label_font = font.Font(family="Futura", size=30, weight="bold")
        self.seconds_label = tk.Label(
            self.canvas, font=seconds_label_font, fg="gray", bg="black"
        )
        self.seconds_label.pack(side="top", anchor="nw", padx=50)
        self.seconds_label.place(x=315, y=195)

        self.date_label = tk.Label(
            self.canvas, font=("Futura", 25), fg="white", bg="black"
        )
        self.date_label.pack(side="top", anchor="nw", padx=50, pady=(0, 20))

        self.weather_frame = tk.Frame(self.canvas, bg="black")
        self.weather_frame.pack(side="top", anchor="ne", padx=50, pady=50)

        self.weather_icon_label = tk.Label(self.weather_frame, bg="black")
        self.weather_icon_label.pack(side="left", padx=10)

        self.weather_info_frame = tk.Frame(self.canvas, bg="black")
        self.weather_info_frame.pack(side="top", anchor="ne", padx=50, pady=5)
        self.weather_info_frame.grid_columnconfigure(0, weight=1)
        self.weather_main_icon_label = tk.Label(self.weather_info_frame, bg="black")
        self.weather_main_icon_label.grid(row=0, column=0, padx=(0, 10))

        self.weather_temp_label = tk.Label(
            self.weather_info_frame, font=font.Font(family="Futura", size=35, weight="bold"), fg="white", bg="black"
        )
        self.weather_temp_label.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.weather_desc_label = tk.Label(
            self.weather_info_frame, font=("Futura", 35), fg="white", bg="black"
        )
        self.weather_desc_label.grid(row=0, column=2)

        self.weather_line = tk.Frame(self.canvas, bg="gray", height=2, width=250)
        self.weather_line.pack(side="top", anchor="e", padx=50, pady=5)

        self.weather_table_frame = tk.Frame(self.canvas, bg="black")
        self.weather_table_frame.pack(side="right", anchor="ne", padx=50, pady=20)
        self.weather_table_frame.grid_columnconfigure(2, weight=2)

        self.news_label_publisher = tk.Label(
            self.canvas, font=("Futura", 23), fg="gray", bg="black", justify="left"
        )
        self.news_label_publisher.pack(side="bottom", anchor="nw", padx=50, pady=50)
        self.news_label_publisher.config(text=" ~ ")

        self.news_label = tk.Label(
            self.canvas,
            font=("Futura", 30),
            fg="white",
            bg="black",
            wraplength=520,
            justify="left",
        )
        self.news_label.pack(side="bottom", anchor="nw", padx=50)
        self.news_label.config(text="Loading news...")

    def update_clock(self) -> None:
        """
        Updates the on-screen clock
        """

        now = time.localtime()
        self.time = time.strftime("%H:%M", now)
        self.time_seconds = time.strftime("%S", now)
        self.date = time.strftime("%A, %B %d", now)
        self.time_label.config(text=self.time)
        self.seconds_label.config(text=self.time_seconds)
        self.date_label.config(text=self.date)
        self.after(1000, self.update_clock)
    
    def get_country_name(self, country_code: str) -> str:
        """
        Get the country name from the country code
        """

        try:
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name
        except AttributeError:
            return "Country not found"
        
    def update_weather(self) -> None:
        """
        Updates the weather information
        """

        query = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "current": "temperature_2m,is_day,weather_code",
        }
        res = requests.get("https://api.open-meteo.com/v1/forecast", params=query)
        
        if self.debug:
            print(res.content)

        if res.ok:
            data = res.json()
            weather_code = data["current"]["weather_code"]
            is_day = data["current"]["is_day"] == 1
            current_temperature = round(data["current"]["temperature_2m"])

            weather_data = self.get_weather_data(weather_code, is_day)
            self.weather_icon_url = weather_data["icon"]

            self.weather_temp_label.config(text=f"{current_temperature}°C")
            self.weather_desc_label.config(text=weather_data["description"])
            self.display_weather_icons(data["daily"])

            if self.debug:
                print(f"Weather: {current_temperature}°C")

        else:
            self.weather = "Unable to get weather information"
            if self.debug:
                print("Unable to get weather information")
                print(res.json())

            self.weather_temp_label.config(text=self.weather)
            self.after(3600000, self.update_weather)

        self.after(3600000, self.update_weather)

    def get_weather_data(self, weather_code: int, is_day: bool) -> dict:
        """
        Get weather description and icon URL based on weather code and day/night
        """

        with open("weather.json", "r") as f:
            weather_data = json.load(f)

        weather_code_str = str(weather_code)

        time_of_day = "night"
        if is_day:
            time_of_day = "day"            

        if weather_code_str in weather_data:
            return {
                "description": weather_data[weather_code_str][time_of_day][
                    "description"
                ],
                "icon": weather_data[weather_code_str][time_of_day]["image"],
            }
        else:
            print(f"Invalid weather code: {weather_code_str}")
            return {"description": "Unknown", "icon": ""}

    def display_weather_icons(self, daily_data: dict) -> None:
        """
        Display weather icons in the table for the next 6 days
        """

        opacity_hex = [
            "#FFFFFF",
            "#E6E6E6",
            "#CCCCCC",
            "#B3B3B3",
            "#999999",
            "#808080"
        ]

        main_weather_code = daily_data["weather_code"][0]
        main_weather_icon_url = self.get_icon_url(main_weather_code)

        self.load_weather_icon(main_weather_icon_url, self.weather_main_icon_label)

        for i, day_data in enumerate(
            daily_data["weather_code"][1:7]
        ):  # Skip the first day (today)
            icon_code = day_data
            avg_temperature = (
                daily_data["temperature_2m_max"][i + 1]
                + daily_data["temperature_2m_min"][i + 1]
            ) / 2

            icon_url = self.get_icon_url(icon_code)

            icon_label = tk.Label(self.weather_table_frame, bg="black")
            icon_label.grid(row=i, column=0, padx=(0, 10))
            self.load_weather_icon(icon_url, icon_label)
            temp_label = tk.Label(
                self.weather_table_frame,
                text=f"{round(avg_temperature)}°C",
                font=font.Font(family="Futura", size=21, weight="bold"),
                fg=opacity_hex[i],
                bg="black",
                anchor="w"
            )
            temp_label.grid(row=i, column=1, padx=(0, 10), sticky="w")  # Use sticky="e" to align the label to the right

            day = time.strftime('%A', time.localtime(time.time() + (i + 1) * 86400))
            day_label = tk.Label(
                self.weather_table_frame,
                text=f"{day}",
                font=font.Font(family="Futura", size=21),
                fg=opacity_hex[i],
                bg="black",
                anchor="e"
            )
            day_label.grid(row=i, column=2, pady=(5, 0), sticky="e")

    def load_weather_icon(self, icon_url: str, label: tk.Label):
        """
        Load weather icon from URL and display it in the given label
        """

        try:
            response = requests.get(icon_url)
            response.raise_for_status()

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.resize((55, 55), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                label.config(image=img)
                label.image = img
            else:
                print(
                    f"Failed to load weather icon from URL: {icon_url}. HTTP status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"Error loading weather icon from URL: {icon_url}. Exception: {e}")

    def get_icon_url(self, icon_code: int) -> str:
        """
        Get the appropriate icon URL based on the weather code
        """

        with open("weather.json", "r") as f:
            weather_data = json.load(f)

        icon_code_str = str(icon_code)

        if icon_code_str in weather_data:
            return weather_data[icon_code_str]["day"]["image"]
        else:
            print(f"Invalid weather code: {icon_code_str}")
            return ""

    def update_news(self) -> None:
        """
        Fetches the latest news using an API.
        """

        if self.debug:
            headline = {"title": "A kid in Alaska chews on gummy bears as his daily snack.", "publisher": {"title": "CNN"}}
        else:
            gnews = GNews()
            country_name = self.get_country_name(self.country).replace(" ", "%20")
            headline = gnews.get_news_by_location(country_name)[0]

        title = headline['title']
        publisher = headline['publisher']['title']
        title = title.removesuffix(" - " + publisher)

        self.news_label.config(text=title)
        self.news_label_publisher.config(text=" - " + publisher)
        self.after(43200000, self.update_news)



# Create an instance of SmartMirror
app = SmartMirror()
app.mainloop()