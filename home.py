from flask_wtf import FlaskForm

from wtforms import SubmitField, FloatField, SelectField

from wtforms.validators import DataRequired

from flaskr.Modules.cellPostprocessing import postprocess
from flaskr.Modules.simulation import Simulation
from flaskr.Modules.dieselTruck import DieselTruck
from flaskr.Modules.dieselinput import DieselInput
from flaskr.Modules.batteryElectricTruck import BatteryElectricTruck
from flaskr.Modules.sizing import Sizing
from flaskr.Modules.costmodel import Costmodel
from flaskr.Modules.etruckinput import BETInput
from flaskr.Modules.sizinginput import SizingInput
from flaskr.Modules.costinput import CostInput
from flaskr.Modules.method import Method, Method1, Method2, Method3, Method4, Method5, Method6, Method7, Method8, Method9, Method10, Method11, Method12, Method13, Method14, Method15
import pandas as pd
from pandas import read_csv
from pandas import read_excel
import plotly.express as px
import json
import plotly
import plotly.graph_objects as go

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, send_from_directory, send_file
)
from werkzeug.security import check_password_hash, generate_password_hash

dt = DieselTruck() # Diesel truck
bet = BatteryElectricTruck(dt) # Battery electric truck based on diesel truck parameters
drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri")
sim = Simulation(drivingcycle)
size = Sizing(sim)
costmodel = Costmodel()

class StartForm(FlaskForm): 
	mission_profile = SelectField('Mission Profiles', choices=[('Coach'),('Construction'),('HeavyUrban'),('Interurban'),('LongHaul'),
	('MunicipalUtility'),('RegionalDelivery'),('Suburban'),('Urban'),('UrbanDelivery')], default='LongHaul')
	submit = SubmitField("Bestätigen")

# Create a Form Class for diesel truck
class DieselForm(FlaskForm): 
	motor_power = FloatField("Max. Power in [W]", validators=[DataRequired()], default=dt.motor_power)
	fr = FloatField("Rollwiderstandskoeffizient", validators=[DataRequired()], default=dt.fr)
	cd_a = FloatField("Luftwiderstandsbeiwert x Stirnfläche in [m^2]", validators=[DataRequired()], default=dt.cd_a)
	p_aux = FloatField("Nebenverbrauch in [W]", validators=[DataRequired()], default=dt.p_aux)
	vol_pt = FloatField("Volumen des Antriebsstrangs in [L]", validators=[DataRequired()], default=dt.vol_pt)
	m_max = FloatField("Zulässiges Gesamtgewicht des Fahrzeugs in [kg]", validators=[DataRequired()], default=dt.m_max)
	m_szm = FloatField("Masse der Sattelzugmaschine in [kg]", validators=[DataRequired()], default=dt.m_szm)
	m_trailer = FloatField("Masse des Anhängers in [kg]", validators=[DataRequired()], default=dt.m_trailer)
	payload_max = FloatField("Max. Zuladung in [kg]", validators=[DataRequired()], default=dt.payload_max)
	share_low_load = FloatField("Anteil des Niedriglastbetriebs", validators=[DataRequired()], default=dt.share_low_load)
	share_ref_load = FloatField("Anteil des Referenzlastbetriebs", validators=[DataRequired()], default=dt.share_ref_load)
	con = FloatField("Energieverbrauch in [L/km]", validators=[DataRequired()], default=dt.con)
	c_toll = FloatField("Mautkosten in [€/km]", validators=[DataRequired()], default=dt.c_toll)
	imc = FloatField("Beiwert für Indirekte Herstellungskosten", validators=[DataRequired()], default=dt.imc)
	dmc_ice = FloatField("Direkte Herstellungskosten des Motors in [€/kW]", validators=[DataRequired()], default=72)
	dmc_tank = FloatField("Direkte Herstellungskosten des Tanks in [€/L]", validators=[DataRequired()], default=2)
	dmc_eat = FloatField("Direkte Herstellungskosten des Getriebes in [€/kW]", validators=[DataRequired()], default=19.8)
	vol_tank = FloatField("Tankvolumen in [L]", validators=[DataRequired()], default=800)
	c_ice = FloatField("Motorkosten in [€]", validators=[DataRequired()], default=dt.motor_power/1000*72*dt.imc)
	c_tank = FloatField("Tankkosten in [€]", validators=[DataRequired()], default=800*2*dt.imc)
	c_eat = FloatField("Getriebekosten in [€]", validators=[DataRequired()], default=dt.motor_power/1000*19.8*dt.imc)
	c_pt = FloatField("Gesamtkosten des Antriebsstrangs in [€]", validators=[DataRequired()], default=dt.c_pt)
	c_maintenance = FloatField("Wartungskosten in [€/km]", validators=[DataRequired()], default=dt.c_maintenance)
	c_tax = FloatField("Steuern in [€/Jahr]", validators=[DataRequired()], default=dt.c_tax)

	submit = SubmitField("Speichern")


# Create a Form Class for electric truck
class EForm(FlaskForm): 
	motor_power = FloatField("Max Power in [W]", validators=[DataRequired()], default=bet.motor_power)
	fr = FloatField("Rollwiderstandskoeffizient", validators=[DataRequired()], default=bet.fr)
	cd_a = FloatField("Luftwiderstandsbeiwert x Stirnfläche in [m^2]", validators=[DataRequired()], default=bet.cd_a)
	eta = FloatField("Effizienz des Antriebsstrangs", validators=[DataRequired()], default=bet.eta)
	p_aux = FloatField("Nebenverbrauch in [W]", validators=[DataRequired()], default=bet.p_aux)
	m_max = FloatField("Zulässiges Gesamtgewicht des Fahrzeugs in [kg]", validators=[DataRequired()], default=bet.m_max)
	m_drivertrain = FloatField("Masse des Antriebsstrangs in [kg]", validators=[DataRequired()], default=bet.m_drivetrain)
	m_chassis = FloatField("Masse des Fahrgestells in [kg]", validators=[DataRequired()], default=bet.m_chassis)
	m_trailer = FloatField("asse des Anhängers in [kg]", validators=[DataRequired()], default=bet.m_trailer)
	share_low_load = FloatField("Anteil des Niedriglastbetriebs", validators=[DataRequired()], default=bet.share_low_load)
	share_ref_load = FloatField("Anteil des Referenzlastbetriebs", validators=[DataRequired()], default=bet.share_ref_load)
	low_load = FloatField("Niedrige Zuladung in [kg]", validators=[DataRequired()], default=bet.low_load)
	ref_load = FloatField("Referenzzuladung in [kg]", validators=[DataRequired()], default=bet.ref_load)
	dmc_motor = FloatField("Direkte Herstellungskosten des Motors in [€/kW]", validators=[DataRequired()], default=32)
	dmc_pe_hv = FloatField("Direkte Herstellungskosten der Leistungselektronik in [€/kW]", validators=[DataRequired()], default=35)
	c_motor = FloatField("Motorkosten in [€]", validators=[DataRequired()], default=bet.motor_power/1000 * 32 * dt.imc)
	c_pe = FloatField("Kosten der Leistungselektronik in [€]", validators=[DataRequired()], default=bet.motor_power/1000 * 35 * dt.imc)
	c_pt = FloatField("Kosten des Antriebsstrangs in [€]", validators=[DataRequired()], default=bet.motor_power/1000 * 32 * dt.imc+bet.motor_power/1000 * 35 * dt.imc)
	c_toll= FloatField("Mautkosten in [€/km]", validators=[DataRequired()], default=bet.c_toll)
	c_maintenance = FloatField("Wartungskosten in [€/km]", validators=[DataRequired()], default=bet.c_maintenance)
	c_tax = FloatField("Steuern in [€/Jahr]", validators=[DataRequired()], default=bet.c_tax)
	bat_scrappage = FloatField("Restwert der Batterie am Ende der Lebensdauer in %", validators=[DataRequired()], default=bet.bat_scrappage)

	submit = SubmitField("Speichern")

# Create a Form Class for cost model and battery sizing
class Costmodel(FlaskForm): 
	servicelife = FloatField("Betriebsdauer in Jahren", validators=[DataRequired()], default=costmodel.servicelife)
	annual_mileage = FloatField("Jährlicher Kilometerstand in [km]", validators=[DataRequired()], default=costmodel.annual_mileage)
	r = FloatField("Zinssatz", validators=[DataRequired()], default=costmodel.r)
	c_cell2system = FloatField("Skalierungsfaktor zwischen Zellen und System", validators=[DataRequired()], default=costmodel.c_cell2system)
	c_diesel = FloatField("Kosten für Diesel in [€/L]", validators=[DataRequired()], default=costmodel.c_diesel)
	c_elec_sc = FloatField("Stromkosten für langsames Laden in [€/kWh]", validators=[DataRequired()], default=costmodel.c_elec_sc)
	c_elec_fc = FloatField("Kosten für Schnellladestrom in [€/kWh]", validators=[DataRequired()], default=0.35/1.19)
	z_fc = FloatField("Anteil der Schnellladung", validators=[DataRequired()], default=costmodel.z_fc)
	t_trip_max = FloatField("Maximale Fahrzeit ohne Pause in [h]", validators=[DataRequired()], default=size.t_trip_max)
	t_day_max = FloatField("Maximale Tagesfahrzeit in [h]", validators=[DataRequired()], default=size.t_day_max)
	t_break = FloatField("Obligatorische Fahrtunterbrechung in [h]", validators=[DataRequired()], default=0.75)
	t_plug_unplug = FloatField("Erforderliche Zeit zum Anschließen und Trennen vom Ladegerät in [h]", validators=[DataRequired()], default=5/60)
	t_fc = FloatField("Verfügbare Zeit für Schnellladung in [h]", validators=[DataRequired()], default=size.t_fc)
	r_oversizing = FloatField("Überdimensionierung der Batterie", validators=[DataRequired()], default=size.r_oversizing)
	cp_share = FloatField("Anteil der Batterie, die mit max. C-Rate aufladen kann", validators=[DataRequired()], default=size.cp_share)
	p_fc = FloatField("Ladeleistung in [kW]", validators=[DataRequired()], default=350)
	
	submit = SubmitField("Speichern")


# Create a Form Class for cell assessment
class BewertungForm(FlaskForm): 
	submit = SubmitField("Bewertung durchführen")

# Create blueprint for homepage
bp = Blueprint('home', __name__, url_prefix='/home')

# Route for homepage
@bp.route('/', methods=['GET', 'POST'])
def index(): 
	session.clear()
	if request.method == 'POST': 
		return redirect(url_for("home.start"))
	else:
		return render_template("index.html")

# Route for simulation page
@bp.route('/start', methods=['GET', 'POST'])
def start(): 
	return render_template("start.html")

# Route for cell database
@bp.route('/start/zelldatenbank', methods=['GET', 'POST'])
def zelldatenbank(): 
	return send_file('inputs/StateOfTheArt_BatteryCells_ISI_TUM_v5.xlsx',download_name='Zelldatenbank.xlsx',as_attachment=True)

# Route for mission profiles
@bp.route('/start/missionprofile', methods=['GET', 'POST'])
def missionprofile(): 
	form = StartForm()
	request_type_str = request.method
	if request_type_str == 'POST': # at the beginning, the parameters have the default value. if the user want to save the new parameters:
		missionProfile = form.mission_profile.data # the new parameters from the form will be saved in variables
		session['missionProfile'] = missionProfile # save in session for the final calculation
		return render_template('start.html', form=form) # after click the save button, the user will go back to the simulation page

	elif session.get('missionProfile') is not None: 
		form.mission_profile.data = session['missionProfile'] # the parameters have been edited before, means the parameters shown in the form are not default values but the last time saved values. 
		return render_template('mission.html', form=form)
	else: # if the user just want to see the mission profile page and does nothing, so here just show the mission profile page with the get methode
		return render_template('mission.html', form=form)

# Route for diesel truck
@bp.route('/start/dieseltruck', methods=['GET', 'POST'])
def dieseltruck():
	form = DieselForm()
	request_type_str = request.method
	if request_type_str == 'POST': # at the beginning, the parameters have the default value. if the user want to save the new parameters:
		session['motor_power'] = form.motor_power.data # save the new parameters from the form in session for the final calculation
		session['fr'] = form.fr.data
		session['cd_a'] = form.cd_a.data
		session['p_aux'] = form.p_aux.data
		session['vol_pt'] = form.vol_pt.data
		session['m_max'] = form.m_max.data
		session['m_szm'] = form.m_szm.data
		session['m_trailer'] = form.m_trailer.data
		session['payload_max'] = form.payload_max.data
		session['share_low_load'] = form.share_low_load.data
		session['share_ref_load'] = form.share_ref_load.data
		session['con'] = form.con.data
		session['c_toll'] = form.c_toll.data
		session['imc'] = form.imc.data
		session['dmc_ice'] = form.dmc_ice.data
		session['dmc_tank'] = form.dmc_tank.data
		session['dmc_eat'] = form.dmc_eat.data
		session['vol_tank'] = form.vol_tank.data
		session['c_ice'] = form.c_ice.data
		session['c_tank'] = form.c_tank.data
		session['c_eat'] = form.c_eat.data
		session['c_pt'] = form.c_pt.data
		session['c_maintenance'] = form.c_maintenance.data
		session['c_tax'] = form.c_tax.data
		return render_template('start.html') # after click the save button, the user will go back to the simulation page
	elif session.get('motor_power') is not None: # the parameters have been edited before, means the parameters shown in the form are not default values but the last time saved values.
		form.motor_power.data = session['motor_power']
		form.fr.data = session['fr']
		form.cd_a.data = session['cd_a']
		form.p_aux.data = session['p_aux']
		form.vol_pt.data = session['vol_pt']
		form.m_max.data = session['m_max']
		form.m_szm.data = session['m_szm']
		form.m_trailer.data = session['m_trailer']
		form.payload_max.data = session['payload_max']
		form.share_low_load.data = session['share_low_load']
		form.share_ref_load.data = session['share_ref_load']
		form.con.data = session['con']
		form.c_toll.data = session['c_toll']
		form.imc.data = session['imc']
		form.dmc_ice.data = session['dmc_ice']
		form.dmc_tank.data = session['dmc_tank']
		form.dmc_eat.data = session['dmc_eat']
		form.vol_tank.data = session['vol_tank']
		form.c_ice.data = session['c_ice']
		form.c_tank.data = session['c_tank']
		form.c_eat.data = session['c_eat']
		form.c_pt.data = session['c_pt']
		form.c_maintenance.data = session['c_maintenance']
		form.c_tax.data = session['c_tax']
		return render_template('dieseltruck.html', form=form)
	else: # if the user just want to see the diesel truck page and does nothing, so here just show the diesel truck page with the get methode
		return render_template('dieseltruck.html', form=form)

# Route for battery electric truck
@bp.route('/start/e-truck', methods=['GET', 'POST'])
def e_truck(): 
	form = EForm()
	request_type_str = request.method
	if request_type_str == 'POST': # at the beginning, the parameters have the default value. if the user want to save the new parameters:
		session['e_motor_power'] = form.motor_power.data # save the new parameters from the form in session for the final calculation
		session['e_fr'] = form.fr.data
		session['e_cd_a'] = form.cd_a.data
		session['e_eta'] = form.eta.data
		session['e_p_aux'] = form.p_aux.data
		session['e_m_max'] = form.m_max.data
		session['e_m_drivertrain'] = form.m_drivertrain.data
		session['e_m_chassis'] = form.m_chassis.data
		session['e_m_trailer'] = form.m_trailer.data
		session['e_share_low_load'] = form.share_low_load.data
		session['e_share_ref_load'] = form.share_ref_load.data
		session['e_low_load'] = form.low_load.data
		session['e_ref_load'] = form.ref_load.data
		session['dmc_motor'] = form.dmc_motor.data
		session['dmc_pe_hv'] = form.dmc_pe_hv.data
		session['c_motor'] = form.c_motor.data
		session['c_pe'] = form.c_pe.data
		session['e_c_pt'] = form.c_pt.data
		session['e_c_toll'] = form.c_toll.data
		session['e_c_maintenance'] = form.c_maintenance.data
		session['e_c_tax'] = form.c_tax.data
		session['bat_scrappage'] = form.bat_scrappage.data
		return render_template('start.html') # after click the save button, the user will go back to the simulation page
	elif session.get('e_motor_power') is not None: # the parameters have been edited before, means the parameters shown in the form are not default values but the last time saved values.
		form.motor_power.data = session['e_motor_power']
		form.fr.data = session['e_fr']
		form.cd_a.data = session['e_cd_a']
		form.eta.data = session['e_eta']
		form.p_aux.data = session['e_p_aux']
		form.m_max.data = session['e_m_max']
		form.m_drivertrain.data = session['e_m_drivertrain']
		form.m_chassis.data = session['e_m_chassis']
		form.m_trailer.data = session['e_m_trailer']
		form.share_low_load.data = session['e_share_low_load']
		form.share_ref_load.data = session['e_share_ref_load']
		form.low_load.data = session['e_low_load']
		form.ref_load.data = session['e_ref_load']
		form.dmc_motor.data = session['dmc_motor']
		form.dmc_pe_hv.data = session['dmc_pe_hv']
		form.c_motor.data = session['c_motor']
		form.c_pe.data = session['c_pe']
		form.c_pt.data = session['e_c_pt']
		form.c_toll.data = session['e_c_toll']
		form.c_maintenance.data = session['e_c_maintenance']
		form.c_tax.data = session['e_c_tax']
		form.bat_scrappage.data = session['bat_scrappage']
		return render_template("e_truck.html", form=form)
	else: # if the user just want to see the battery electric truck page and does nothing, so here just show the battery electric truck page with the get methode
		return render_template("e_truck.html", form=form)

# Route for cost model and battery sizing
@bp.route('/start/costmodel', methods=['GET', 'POST'])
def cost(): 
	form = Costmodel()
	request_type_str = request.method
	if request_type_str == 'POST': # at the beginning, the parameters have the default value. if the user want to save the new parameters:
		session['servicelife'] = form.servicelife.data # save the new parameters from the form in session for the final calculation
		session['annual_mileage'] = form.annual_mileage.data
		session['r'] = form.r.data
		session['c_cell2system'] = form.c_cell2system.data
		session['c_diesel'] = form.c_diesel.data
		session['c_elec_sc'] = form.c_elec_sc.data
		session['c_elec_fc'] = form.c_elec_fc.data
		session['z_fc'] = form.z_fc.data
		session['t_trip_max'] = form.t_trip_max.data
		session['t_day_max'] = form.t_day_max.data
		session['t_break'] = form.t_break.data
		session['t_plug_unplug'] = form.t_plug_unplug.data
		session['t_fc'] = form.t_fc.data
		session['p_fc'] = form.p_fc.data
		session['r_oversizing'] = form.r_oversizing.data
		session['cp_share'] = form.cp_share.data
		return render_template('start.html') # after click the save button, the user will go back to the simulation page
	elif session.get('servicelife') is not None: # the parameters have been edited before, means the parameters shown in the form are not default values but the last time saved values.
		form.servicelife.data = session['servicelife']
		form.annual_mileage.data = session['annual_mileage']
		form.r.data = session['r']
		form.c_cell2system.data = session['c_cell2system']
		form.c_diesel.data = session['c_diesel']
		form.c_elec_sc.data = session['c_elec_sc']
		form.c_elec_fc.data = session['c_elec_fc']
		form.z_fc.data = session['z_fc']
		form.t_trip_max.data = session['t_trip_max']
		form.t_day_max.data = session['t_day_max']
		form.t_break.data = session['t_break']
		form.t_plug_unplug.data = session['t_plug_unplug']
		form.t_fc.data = session['t_fc']
		form.p_fc.data = session['p_fc']
		form.r_oversizing.data = session['r_oversizing']
		form.cp_share.data = session['cp_share']
		return render_template("costmodel.html", form=form)
	else: # if the user just want to see the cost model page and does nothing, so here just show the cost model page with the get methode
		return render_template("costmodel.html", form=form)

# Route to show result
@bp.route('/start/Result', methods=['GET', 'POST'])
def result(): 
	cells_raw = read_excel("flaskr/inputs/StateOfTheArt_BatteryCells_ISI_TUM_v5.xlsx") #Load cell database
	cells = postprocess(cells_raw) #Post process cell data

	if session.get('motor_power') is None and session.get('missionProfile') is None and session.get('e_motor_power') is None and session.get('servicelife') is None: # if the user edited nothing and carry out the calculation direktly
		method_350kW = Method() #Initialize method
		results_350kW = method_350kW.eval_cells(cells) #Execute for cells in database

		result = results_350kW
	
	elif session.get('motor_power') is not None and session.get('missionProfile') is None and session.get('e_motor_power') is None and session.get('servicelife') is None: # if user only edited the parameters of diesel truck

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'], # hand over the new parameters from the form to define diesel truck
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		method = Method1(dt) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results
		

	elif session.get('motor_power') is None and session.get('missionProfile') is not None and session.get('e_motor_power') is None and session.get('servicelife') is None: # if user only changed the mission profile
		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle
		
		method = Method2(drivingcycle) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is None and session.get('e_motor_power') is not None and session.get('servicelife') is None: # if user only edited the parameters of battery electric truck
		
		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		method = Method3(bet) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is None and session.get('e_motor_power') is None and session.get('servicelife') is not None: # if user only edited the parameters of cost model or battery sizing
		drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") #Load longhaul driving cycle
		sim = Simulation(drivingcycle) #Longhaul simulation
		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		p_fc = session['p_fc']
		method = Method4(drivingcycle,sim,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is not None and session.get('missionProfile') is not None and session.get('e_motor_power') is None and session.get('servicelife') is None: # if user edited the parameters of diesel truck and mission profile
		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle
		
		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])
		
		method = Method5(drivingcycle,dt) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is not None and session.get('missionProfile') is None and session.get('e_motor_power') is not None and session.get('servicelife') is None: # if user edited the parameters of diesel truck and battery electric truck

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		method = Method6(dt,bet) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results
		

	elif session.get('motor_power') is not None and session.get('missionProfile') is None and session.get('e_motor_power') is None and session.get('servicelife') is not None: # if user edited the parameters of diesel truck and cost model or battery sizing
		drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") #Load longhaul driving cycle
		sim = Simulation(drivingcycle) #Longhaul simulation

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])
		p_fc = session['p_fc']
		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method7(drivingcycle,sim,dt,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is not None and session.get('e_motor_power') is not None and session.get('servicelife') is None: # if user edited the parameters of battery electric truck and mission profile

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle
		
		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		method = Method8(drivingcycle,bet) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is not None and session.get('e_motor_power') is None and session.get('servicelife') is not None: # if user edited the parameters of mission profile and cost model or battery sizing

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle

		p_fc = session['p_fc']
		sim = Simulation(drivingcycle) 
		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method9(drivingcycle,sim,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is None and session.get('e_motor_power') is not None and session.get('servicelife') is not None: # if user edited the parameters of battery electric truck and cost model or battery sizing
		drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") #Load longhaul driving cycle
		sim = Simulation(drivingcycle) #Longhaul simulation
		p_fc = session['p_fc']

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method10(drivingcycle,sim,bet,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database
		
		result = results


	elif session.get('motor_power') is not None and session.get('missionProfile') is not None and session.get('e_motor_power') is not None and session.get('servicelife') is None: # if user edited the parameters of diesel truck, mission profile and battery electric truck

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		method = Method11(drivingcycle,dt,bet) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is not None and session.get('missionProfile') is not None and session.get('e_motor_power') is None and session.get('servicelife') is not None: # if user edited the parameters of diesel truck, mission profiles and cost model or battery sizing

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle

		sim = Simulation(drivingcycle)
		p_fc = session['p_fc']

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method12(drivingcycle,sim,dt,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results

	elif session.get('motor_power') is not None and session.get('missionProfile') is None and session.get('e_motor_power') is not None and session.get('servicelife') is not None: # if user edited the parameters of diesel truck, battery electric truck and cost model or battery sizing
		drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") #Load longhaul driving cycle
		sim = Simulation(drivingcycle) #Longhaul simulation
		p_fc = session['p_fc']

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method13(drivingcycle,sim,dt,bet,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is None and session.get('missionProfile') is not None and session.get('e_motor_power') is not None and session.get('servicelife') is not None: # if user edited the parameters of mission profiles, battery electric truck and cost model or battery sizing

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle

		sim = Simulation(drivingcycle)
		p_fc = session['p_fc']

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method14(drivingcycle,sim,bet,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database

		result = results


	elif session.get('motor_power') is not None and session.get('missionProfile') is not None and session.get('e_motor_power') is not None and session.get('servicelife') is not None: # if user edited the parameters of all models

		if session['missionProfile'] == 'Coach': 
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Coach.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Construction':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Construction.vdri") # Load driving cycle
		elif session['missionProfile'] == 'HeavyUrban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/HeavyUrban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Interurban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Interurban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'LongHaul':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/LongHaul.vdri") # Load driving cycle
		elif session['missionProfile'] == 'MunicipalUtility':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/MunicipalUtility.vdri") # Load driving cycle
		elif session['missionProfile'] == 'RegionalDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/RegionalDelivery.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Suburban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Suburban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'Urban':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/Urban.vdri") # Load driving cycle
		elif session['missionProfile'] == 'UrbanDelivery':
			drivingcycle = read_csv("flaskr/inputs/Mission Profiles/UrbanDelivery.vdri") # Load driving cycle

		sim = Simulation(drivingcycle)
		p_fc = session['p_fc']

		dt = DieselInput(session['motor_power'],session['fr'],session['cd_a'],session['p_aux'],session['vol_pt'],session['m_max'],session['m_szm'],session['m_trailer'],session['payload_max'],
		session['share_low_load'],session['share_ref_load'],session['con'],session['c_toll'],session['c_tax'],session['c_maintenance'],session['imc'],
		session['dmc_ice'],session['dmc_tank'],session['dmc_eat'],session['vol_tank'],session['c_ice'],session['c_tank'],session['c_eat'],session['c_pt'])

		bet = BETInput(session['e_motor_power'],session['e_fr'],session['e_cd_a'],session['e_p_aux'],session['e_eta'],session['e_m_max'],session['e_m_chassis'],session['e_m_drivertrain'],session['e_m_trailer'],session['e_share_low_load'],
		session['e_share_ref_load'],session['e_low_load'],session['e_ref_load'],session['dmc_motor'],session['dmc_pe_hv'],session['c_motor'],session['c_pe'],session['e_c_pt'],session['e_c_toll'],session['e_c_tax'],session['e_c_maintenance'],
		session['bat_scrappage'])

		sizing = SizingInput(sim,session['t_trip_max'],session['t_day_max'],session['t_break'],session['t_plug_unplug'],session['t_fc'],session['r_oversizing'],session['cp_share'])
		costmodel = CostInput(int(session['servicelife']),session['annual_mileage'],session['r'],session['c_cell2system'],session['c_diesel'],session['c_elec_sc'],session['c_elec_fc'],session['z_fc'])
		method = Method15(drivingcycle,sim,dt,bet,sizing,costmodel,p_fc) #Initialize method
		results = method.eval_cells(cells) #Execute for cells in database
		
		result = results


	fig = px.scatter(result, x="maxpayload", y="cpar", color="Format", symbol="Chemistry", 
					labels={
                     "maxpayload": "Maximale Zuladung [kg]",
                     "cpar": "Kostenparitätspreis [€/kWh]",
					 "Unom": "Nennspannung [V]", 
					 "Capacity": "Kapazität [Ah]", 
					 "ncycle": "Zyklenfestigkeit",
					 "EOL": "Verbleibende Kapazität im letzten Zyklus", 
					 "mspec": "Massspezifische Energie [Wh/kg]", 
					 "rho_bat": "Volumetrische Energiedichte [Wh/L]", 
					 "Ccharge": "C-Rate"
                 	},
					hover_data={"Company","Name","Chemistry","Unom","Format","Capacity","ncycle","EOL","mspec","rho_bat","Ccharge"})

	fig.add_vline(x=method.bet.ref_load, line_dash="dash", line_color="green", annotation_text="Reference load", annotation_position="top left", annotation_textangle = 90)
	fig.add_vline(x=method.dt.payload_max, line_dash="dash", line_color="green", annotation_text="Max. payload", annotation_position="top right", annotation_textangle = 90)
	fig.update_layout(
    font=dict(
        family="Arial",
        size=15,
    	)
	)
	graph1JSON = json.dumps(fig, cls = plotly.utils.PlotlyJSONEncoder)	

	fig2 = px.scatter(result, x="Vbat", y="cpar", color="Format", symbol="Chemistry", 
					labels={
                     "Vbat": "Batterievolumen [L]",
                     "cpar": "Kostenparitätspreis [€/kWh]",
					 "Unom": "Nennspannung [V]", 
					 "Capacity": "Kapazität [Ah]", 
					 "ncycle": "Zyklenfestigkeit",
					 "EOL": "Verbleibende Kapazität im letzten Zyklus", 
					 "mspec": "Massspezifische Energie [Wh/kg]", 
					 "rho_bat": "Volumetrische Energiedichte [Wh/L]", 
					 "Ccharge": "C-Rate"
                 	},
					hover_data={"Company","Name","Chemistry","Unom","Format","Capacity","ncycle","EOL","mspec","rho_bat","Ccharge"})
	fig2.add_vline(x=method.dt.vol_pt, line_dash="dash", line_color="green", annotation_text="Volumen des Antriebsstrangs von Diesel Lkw", annotation_position="top left", annotation_textangle = 90)	
	fig2.update_layout(
    font=dict(
        family="Arial",
        size=15,
    	)
	)
	graph2JSON = json.dumps(fig2, cls = plotly.utils.PlotlyJSONEncoder)

	return render_template('result_test.html', graph1JSON=graph1JSON, graph2JSON=graph2JSON)