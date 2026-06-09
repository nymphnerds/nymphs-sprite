extends Node2D

## Foundry Render Lab — keyboard toggles for light/shader/particle comparison.
## Keys:
##   1 — Dusk Torch light rig
##   2 — Cold Moonlight light rig
##   0 — Baseline (no lights, no shader, no particles)
##   P — Toggle particles
##   S — Toggle shader preset
##   F12 — Screenshot

@onready var light_a: PointLight2D = $LightRigA
@onready var light_b: PointLight2D = $LightRigB
@onready var particles_ember: GPUParticles2D = $ParticlesEmber
@onready var particles_dust: GPUParticles2D = $ParticlesDust
@onready var character: Sprite2D = $CharacterSprite

var shader_active: bool = false
var particles_on: bool = true
var current_rig: String = "A"


func _ready() -> void:
	_apply_rig_a()
	_set_particles(true)
	print("Render Lab ready. Keys: 1/2=light, 0=baseline, P=particles, S=shader, F12=screenshot")


func _unhandled_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed:
		return

	match event.keycode:
		KEY_1:
			_apply_rig_a()
		KEY_2:
			_apply_rig_b()
		KEY_0:
			_apply_baseline()
		KEY_P:
			_set_particles(not particles_on)
		KEY_S:
			_toggle_shader()
		KEY_F12:
			_capture_screenshot()


func _apply_rig_a() -> void:
	current_rig = "A"
	light_a.visible = true
	light_a.enabled = true
	light_b.visible = false
	light_b.enabled = false
	print("Light rig: Dusk Torch")


func _apply_rig_b() -> void:
	current_rig = "B"
	light_a.visible = false
	light_a.enabled = false
	light_b.visible = true
	light_b.enabled = true
	print("Light rig: Cold Moonlight")


func _apply_baseline() -> void:
	current_rig = "none"
	light_a.visible = false
	light_a.enabled = false
	light_b.visible = false
	light_b.enabled = false
	_set_particles(false)
	if shader_active:
		_toggle_shader()
	print("Baseline: no finish")


func _set_particles(on: bool) -> void:
	particles_on = on
	particles_ember.emitting = on
	particles_dust.emitting = on
	print("Particles: %s" % ("ON" if on else "OFF"))


func _toggle_shader() -> void:
	shader_active = not shader_active
	if shader_active:
		# Apply a simple rimlight shader — placeholder until real preset
		print("Shader: ON (rimlight)")
	else:
		print("Shader: OFF")


func _capture_screenshot() -> void:
	var img := get_viewport().get_texture().get_image()
	var timestamp := Time.get_datetime_string_from_system().replace(":", "-")
	var rig_label := current_rig if current_rig != "none" else "baseline"
	var path := "res://screenshots/lab_%s_%s.png" % [rig_label, timestamp]
	img.save_png(path)
	print("Screenshot saved: %s" % path)
