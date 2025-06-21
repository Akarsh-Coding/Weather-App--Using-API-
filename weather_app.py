import tkinter as tk
from tkinter import ttk
import geonamescache
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageFilter

from time import strftime



# ------------------------------------------------------------------
# Build ❰country → [city list]❱ mapping once at start‑up using geonamescache
# ------------------------------------------------------------------
gc = geonamescache.GeonamesCache()
countries = gc.get_countries()              # Country code → Country info
cities = gc.get_cities()                    # City ID → City info

# Map country code to country name
code_to_name = {code: data['name'] for code, data in countries.items()}

# Group cities under each country name
country_cities = {}
for city in cities.values():
    cname = code_to_name.get(city['countrycode'])
    if cname:  # Skip unknown/rare country codes
        country_cities.setdefault(cname, []).append(city['name'])

# Sort cities in each country and sort country list for combobox
for lst in country_cities.values():
    lst.sort()
sorted_country_names = sorted(country_cities.keys())

# ------------------------------------------------------------------
# Main Weather Application Class
# ------------------------------------------------------------------
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App")
        self.root.geometry("512x512")
        self.root.resizable(False, False)

        # -------------------------------------------------------------
        # Set background image on canvas
        # -------------------------------------------------------------

        # # Set the background image here by updating the filename in the img_bg path.
        # Available options: "bg01.jpg", "bg02.jpg", or "bg03.jpg".

        img_bg = Image.open("bg03.jpg").resize((512, 512), Image.Resampling.LANCZOS)
        self.photo_bg = ImageTk.PhotoImage(img_bg)

        self.canvas = tk.Canvas(root, width=512, height=512, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.photo_bg, anchor="nw")

        # -------------------------------------------------------------
        # Draw title text on canvas
        # -------------------------------------------------------------
        title_font = ("Monotype Corsiva", 40, "bold") if "Monotype Corsiva" in tkfont.families() else ("Times New Roman", 40, "bold")
        self.canvas.create_text(256, int(512 * 0.15), text="Weather", font=title_font, fill="#000000", anchor="center")

        # -------------------------------------------------------------
        # Create glass-effect frame by blurring part of background
        # -------------------------------------------------------------
        frame_relw = 0.625  # Width ratio
        frame_relh = 0.70   # Height ratio
        frame_w = int(512 * frame_relw)
        frame_h = int(512 * frame_relh)
        frame_x0 = int((512 - frame_w) / 2)
        frame_y0 = int(512 * 0.575 - frame_h / 2)

        # Apply Gaussian blur to the cropped background region
        crop = img_bg.crop((frame_x0, frame_y0, frame_x0 + frame_w, frame_y0 + frame_h))
        crop_blur = crop.filter(ImageFilter.GaussianBlur(radius=7))
        self.frame_bg = ImageTk.PhotoImage(crop_blur)

        self.frame = tk.Frame(self.root, highlightthickness=0, bd=0)
        self.frame.place(x=frame_x0, y=frame_y0, width=frame_w, height=frame_h)

        # Canvas inside the glass frame to display weather info
        self.text_canvas = tk.Canvas(self.frame, highlightthickness=0, bd=0)
        self.text_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.text_canvas.create_image(0, 0, image=self.frame_bg, anchor="nw")

        # -------------------------------------------------------------
        # Style and dropdown widgets for country and city selection
        # -------------------------------------------------------------
        style = ttk.Style()
        style.theme_use('alt')
        style.configure("CustomCombobox.TCombobox", padding=5, background="#007bff", foreground="#050505",
                        arrowcolor="#000000", font=("Times New Roman", 18, "bold"))

        self.city_name = tk.StringVar()
        self.country_name = tk.StringVar()

        # Country combobox
        self.country = ttk.Combobox(self.frame, style="CustomCombobox.TCombobox", width=20,
                                    values=sorted_country_names, state="readonly", textvariable=self.country_name)
        self.country.place(relx=0.25, rely=0.075, anchor="center")
        self.country.set("Select Country")
        self.country.bind("<<ComboboxSelected>>", self._update_cities)

        # City combobox
        self.city = ttk.Combobox(self.frame, style="CustomCombobox.TCombobox", width=20,
                                    values=[""], state="readonly", textvariable=self.city_name)
        self.city.place(relx=0.75, rely=0.075, anchor="center")
        self.city.set("Select City")

        # Weather fetch button
        btn = tk.Button(self.frame, text="Get Weather", font=("Times New Roman", 12, "bold"),
                        bg="#2196F3", fg="#FFFFFF",
                        # command=self.,
                        activebackground="#2196F3", activeforeground="#FFFFFF",)
                        
        btn.place(rely=0.18, relx=0.8, anchor="center")

        # -------------------------------------------------------------
        # Create text placeholders for weather data (location, temp, etc.)
        # -------------------------------------------------------------
        # (All self.text_canvas.create_text… are for display labels and values)

        self.location_val = self.text_canvas.create_text(frame_w * 0.275, frame_h * 0.29,fill="#FFFC36",
                        text="📍 Location", font=("Times New Roman", 18, "bold"), anchor="center")
        self.Description_val = self.text_canvas.create_text(frame_w * 0.35, frame_h * 0.4, fill="#50FF50",
                        text="Description", font=("Times New Roman", 20, "bold"),  anchor="center")
        self.Detail_val = self.text_canvas.create_text(frame_w * 0.75, frame_h * 0.4, text="", 
                        font=("Times New Roman", 16), fill="#50FF50", anchor="center")

        # Temperature details
        Temp_lbl = self.text_canvas.create_text(frame_w * 0.215, frame_h * 0.525, text="Temperature:",
                        font=("Times New Roman", 15, "bold"), fill="#000080")
        self.Temp_val = self.text_canvas.create_text(frame_w * 0.7, frame_h * 0.525, 
                                        text="", font=("Inter", 13), fill="#FFFFFF")

        # Min and Max temperatures
        Min_lbl = self.text_canvas.create_text(frame_w * 0.15, frame_h * 0.575, text="Min:", 
                                    font=("Times New Roman", 15, "bold"), fill="#000080")
        self.Min_val = self.text_canvas.create_text(frame_w * 0.315, frame_h * 0.575, text="",
                                    font=("Inter", 13), fill="#FFFFFF")
        separator = self.text_canvas.create_text(frame_w * 0.5, frame_h * 0.575, text="|",
                                    font=("Inter", 16, "bold"), fill="#C8C8C8")
        Max_lbl = self.text_canvas.create_text(frame_w * 0.65, frame_h * 0.575, text="Max:", 
                                    font=("Times New Roman", 15, "bold"), fill="#000080")
        self.Max_val = self.text_canvas.create_text(frame_w * 0.815, frame_h * 0.575, text="",
                                    font=("Inter", 13), fill="#FFFFFF")

        # AQI (Air Quality Index)
        airQuality_lbl = self.text_canvas.create_text(frame_w * 0.4, frame_h * 0.65, text="AQI:",
                                font=("Times New Roman", 15, "bold"), fill="#000080")
        self.airQuality_val = self.text_canvas.create_text(frame_w * 0.6, frame_h * 0.65, text="",
                                font=("Times New Roman", 14, "bold"), fill="#ffffff")

        # Humidity, Wind, Cloud, Visibility
        humidity_lbl = self.text_canvas.create_text(frame_w * 0.16, frame_h * 0.725, text="Humidity:",
                                            font=("Times New Roman", 15, "bold"), fill="#000080")
        self.humidity_val = self.text_canvas.create_text(frame_w * 0.375, frame_h * 0.725, text="",
                                            font=("Inter", 13), fill="#FFFFFF")
        wind_lbl = self.text_canvas.create_text(frame_w * 0.58, frame_h * 0.725, text="Wind:",
                                            font=("Times New Roman", 15, "bold"), fill="#000080")
        self.wind_val = self.text_canvas.create_text(frame_w * 0.825, frame_h * 0.725, text="",
                                            font=("Inter", 13), fill="#FFFFFF")
        Cloud_lbl = self.text_canvas.create_text(frame_w * 0.19, frame_h * 0.775, text="Cloud Cover:",
                                            font=("Times New Roman", 15, "bold"), fill="#000080")
        self.Cloud_val = self.text_canvas.create_text(frame_w * 0.45, frame_h * 0.775, text="",
                                            font=("Inter", 13), fill="#FFFFFF")
        Visibility_lbl = self.text_canvas.create_text(frame_w * 0.675, frame_h * 0.775, text="Visibility:",
                                            font=("Times New Roman", 15, "bold"), fill="#000080")
        self.Visibility_val = self.text_canvas.create_text(frame_w * 0.9, frame_h * 0.775, text="",
                                            font=("Inter", 13), fill="#FFFFFF")

        # Sunrise, Sunset, Date, Time
        Sunrise_lbl = self.text_canvas.create_text(frame_w * 0.12, frame_h * 0.9, text="Sunrise:",
                                    font=("Times New Roman", 15, "bold"), fill="#000000")
        self.Sunrise_val = self.text_canvas.create_text(frame_w * 0.35, frame_h * 0.9, text="",
                                    font=("Times New Roman", 13, "bold"), fill="#FFFFFF")
        Sunset_lbl = self.text_canvas.create_text(frame_w * 0.12, frame_h * 0.95, text="Sunset:",
                                    font=("Times New Roman", 15, "bold"), fill="#000000")
        self.Sunset_val = self.text_canvas.create_text(frame_w * 0.35, frame_h * 0.95, text="",
                                    font=("Times New Roman", 13, "bold"), fill="#FFFFFF")
        Time_val = self.text_canvas.create_text(frame_w * 0.8, frame_h * 0.9, text="",
                                    font=("Times New Roman", 13, "bold"), fill="#000000")
        Date_val = self.text_canvas.create_text(frame_w * 0.8, frame_h * 0.95, text="",
                                    font=("Times New Roman", 13, "bold"), fill="#000000")

        # -------------------------------------------------------------
        # Real-time time and date display
        # -------------------------------------------------------------
        def show_time():
            self.text_canvas.itemconfig(Time_val, text=strftime('%I:%M:%S %p'))
            self.text_canvas.after(1000, show_time)

        def show_date():
            self.text_canvas.itemconfig(Date_val, text=strftime('%a, %d‑%m‑%Y'))
            self.text_canvas.after(60000, show_date)

        show_date()
        show_time()

    # Update city list based on selected country
    def _update_cities(self, *_):
        country = self.country.get()
        city_list = country_cities.get(country, [])
        self.city["values"] = city_list
        if city_list:
            self.city.set("Select City")


# -------------------------------------------------------------
# Run the application
# -------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()