from django import forms

class TruckParamsForm(forms.Form):
    speed = forms.FloatField(label="Velocidad media (km/h)", initial=120.0)
    cost_per_km = forms.FloatField(label="Coste por km", initial=0.5)
    capacity = forms.IntegerField(label="Capacidad del camión (unidades)", initial=60000)
