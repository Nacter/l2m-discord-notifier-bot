import numpy as np
import timedelta
from datetime import datetime as dt
from datetime import timedelta as td

class Boss():
    def __init__(self, original_name, name, chance, location, respawn_hours):
        self.original_name = str(original_name.lower())
        self.name = str(name)
        self.chance = int(chance)
        self.location = str(location)
        self.respawn_hours = int(respawn_hours)
        self._generate_sound_names()

    def _generate_sound_names(self):
        self.sound_5min = "_".join([self.original_name.lower().replace(" ","-"),"5min"])
        self.sound_appear = "_".join([self.original_name.lower().replace(" ","-"),"appear"])
        
    def __lt__(self, other):
        return self.respawn_time_seconds < other.respawn_time_seconds

    def calc_respawn_time(self, force=False, respawn_time=None):
        self.respawn_time = (respawn_time if force else dt.now()) + td(hours=self.respawn_hours) - td(seconds=1)
        self.respawn_time_seconds = self.respawn_time.timestamp()

    def last_time(self):
        duration =  timedelta.Timedelta(self.respawn_time - dt.now())
        is_valid = self.respawn_time > dt.now()
        days, seconds = duration.days, duration.seconds
        hours = days * 24 + seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return (hours, minutes, seconds, is_valid)
    
    def boss_tagged_str(self):
        (hours, minutes, seconds, _) = self.last_time()
        return(f"Boss **{self.name}** muerto!\nRecordatorio en {hours}h {minutes}m {seconds}s")

    def boss_status_str(self):
        (hours, minutes, seconds, is_valid) = self.last_time()
        moscow_time = self.respawn_time.strftime('%H:%M:%S') 
        if is_valid and hours == 0 and minutes == 0 and seconds == 0:
            return(f"{moscow_time} **{self.name}** apareció en {self.location}  | prob. {self.chance}% | {moscow_time} GMT+1")
        elif is_valid:
            return(f"**{self.name}** en {self.location} dentro de {hours}h {minutes}m {seconds}s | prob. {self.chance}% | {moscow_time} GMT+1")
        else: 
            return(f"**{self.name}** ya fue hace {59-minutes}m {59-seconds}s  | prob {self.chance}% | {moscow_time} GMT+1")

    def export_msg(self):
        date_str = self.respawn_time.strftime('%Y-%m-%d %H:%M:%S') 
        return(f"+{self.name.lower()} {date_str}")

    @staticmethod
    def from_export_str(astring, is_manual=False):
        line = astring.split()
        boss_name = str(line[0][1:])
        resp_last = str(" ".join(line[1:]))
        boss = bosses_dict.get(boss_name.lower())
        resp_last = dt.fromisoformat(resp_last) if is_manual else dt.fromisoformat(resp_last) - td(hours=boss.respawn_hours)
        boss.calc_respawn_time(force=True, respawn_time=resp_last)
        return boss

    def not_tagged(self):
        return(f"**{self.name}** debería haber aparecido\escribe +{self.name.lower()} para restablecer el temporizador.")

    def boss_short_str(self):
        return(f"**{self.name}**")

    def __str__(self):
        return (f"{self.name}|{self.chance}|{self.location}|{self.respawn_hours}\n{self.respawn_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
data = np.genfromtxt('./assets/data/bosses.csv', names=True, delimiter=',', dtype=None, encoding='utf8')
bosses_dict = dict(list(map(lambda x: (x[4], Boss(x[1], x[4], x[2], x[5], x[3])), data)))
