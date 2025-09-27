import time
import threading
from plyer import notification
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from datetime import datetime, timedelta

# Alarm and voice files
ALARM_FILE = "alarm.wav"
MED_VOICES = {
    "Red Cap": "MED_VOICES/red.mp3",
    "Green Cap": "MED_VOICES/green.mp3",
    "Gray Cap": "MED_VOICES/gray.mp3"
}

# Medicine info: color only
MED_INFO = {
    "Red Cap": {"color": (1, 0, 0, 1)},
    "Green Cap": {"color": (0, 1, 0, 1)},
    "Gray Cap": {"color": (0.5, 0.5, 0.5, 1)}
}

reminders = []
current_sounds = []  # list to hold all currently playing sounds

def play_alarm_for_medicine(med_name):
    """Play alarm.wav + medicine voice simultaneously"""
    global current_sounds
    alarm_sound = SoundLoader.load(ALARM_FILE)
    voice_file = MED_VOICES.get(med_name)
    voice_sound = SoundLoader.load(voice_file) if voice_file else None

    current_sounds = []
    if alarm_sound:
        alarm_sound.loop = True
        alarm_sound.play()
        current_sounds.append(alarm_sound)
    if voice_sound:
        voice_sound.loop = True
        voice_sound.play()
        current_sounds.append(voice_sound)

def stop_alarm():
    global current_sounds
    for s in current_sounds:
        if s:
            s.stop()
    current_sounds = []

def update_label(label, r):
    label.text = f"Take {r['name']}"
    label.color = MED_INFO.get(r["name"], {}).get("color", (1,1,1,1))

def reminder_checker(label):
    while True:
        now = datetime.now()
        for r in reminders:
            if now >= r["next_time"]:
                notification.notify(title="Medicine Reminder", message=f"Take {r['name']}")
                Clock.schedule_once(lambda dt, r=r: update_label(label, r))
                threading.Thread(target=lambda: play_alarm_for_medicine(r['name'])).start()
                r["next_time"] += timedelta(hours=r["interval_hours"])
        time.sleep(1)

class MedicineReminderApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(15))
        
        scroll = ScrollView(size_hint=(1, 0.6))
        grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(10), row_default_height=dp(60))
        grid.bind(minimum_height=grid.setter('height'))
        scroll.add_widget(grid)
        
        self.meds = []
        for med_name, info in MED_INFO.items():
            box = BoxLayout(orientation="horizontal", spacing=dp(5), size_hint_y=None, height=dp(50))
            with box.canvas.before:
                Color(*info["color"])
                box.rect = Rectangle(pos=box.pos, size=box.size)
            box.bind(pos=lambda instance, value, r=box: setattr(r.rect, 'pos', r.pos))
            box.bind(size=lambda instance, value, r=box: setattr(r.rect, 'size', r.size))
            
            label = Label(text=med_name, size_hint_x=0.2, bold=True, color=(1,1,1,1))
            interval_input = TextInput(hint_text="Interval (hours)", multiline=False, size_hint_x=0.2)
            duration_days_input = TextInput(hint_text="Days", multiline=False, size_hint_x=0.25)
            duration_weeks_input = TextInput(hint_text="Weeks", multiline=False, size_hint_x=0.25)
            
            box.add_widget(label)
            box.add_widget(interval_input)
            box.add_widget(duration_days_input)
            box.add_widget(duration_weeks_input)
            grid.add_widget(box)
            self.meds.append((med_name, interval_input, duration_days_input, duration_weeks_input))
        
        btn_layout = BoxLayout(size_hint=(1, 0.2), spacing=dp(10))
        add_btn = Button(text="Add All Reminders", background_color=(0, 0.5, 1, 1), font_size=18)
        add_btn.bind(on_press=self.add_reminders)
        stop_btn = Button(text="Stop Alarm", background_color=(1, 0, 0, 1), font_size=18)
        stop_btn.bind(on_press=lambda x: stop_alarm())
        btn_layout.add_widget(add_btn)
        btn_layout.add_widget(stop_btn)
        
        self.label = Label(text="No reminders yet", font_size=24, size_hint=(1, 0.2))
        
        root.add_widget(scroll)
        root.add_widget(btn_layout)
        root.add_widget(self.label)
        
        threading.Thread(target=reminder_checker, args=(self.label,), daemon=True).start()
        
        return root

    def add_reminders(self, instance):
        for med_name, interval_input, days_input, weeks_input in self.meds:
            try:
                interval_hours = float(interval_input.text.strip()) if interval_input.text.strip() else 0.01
            except:
                self.label.text = f"Invalid interval for {med_name}"
                continue
            days = weeks = 0
            try:
                days = int(days_input.text.strip()) if days_input.text.strip() else 0
            except:
                self.label.text = f"Invalid days input for {med_name}"
                continue
            try:
                weeks = int(weeks_input.text.strip()) if weeks_input.text.strip() else 0
            except:
                self.label.text = f"Invalid weeks input for {med_name}"
                continue
            total_days = days + weeks * 7
            if total_days <= 0:
                self.label.text = f"Duration must be >0 for {med_name}"
                continue
            reminders.append({
                "name": med_name,
                "interval_hours": interval_hours,
                "next_time": datetime.now(),
                "end_time": datetime.now() + timedelta(days=total_days)
            })
        self.label.text = "Reminders added for all medicines"

if __name__ == "__main__":
    MedicineReminderApp().run()
