# Entities

## ECS

At the core 'Hub' uses an ECS (Entity Component System) for managing state and functionality of entities.
That means entities are composed of Components that are responsible for a single aspect of an entities' capability
(like a brightness or color components for lamps).

## Creating An Entity

To create an entity simply create a '.yaml' file with the same name ass the entity in the config/entities folder.

### The base configuration for every entity:

````yaml
type: # The entity type (See below)
name: # Optional, used to override the file name as entity name
````

To provide a simple setup process,
there are dedicated device types for the most common device types (like Lamps, plugs etc).
Therefore, The base config doesn't contain much, as the rest of it is heavily dependent on the entity type. <br>

### Entity Types:

To reduce redundancy, most pre-defined device types use the 'control' option to define the underlying I/O service for all components.

#### Lamp:

The 'Lamp' entity type is meant be used for "simple" lamps with only an 'on/off' state.

````yaml
# Simple on/off Light, controlled via MQTT
type: Lamp
control: mqtt.publish
switch:
  topic: test/lamp
````

#### Lamp-dimmable:

The 'Lamp-dimmable' type can be used for dimmable lamps like a philips hue light bulb or a single color RGB-stripe.
The main advantage of using this type is the coupling between the two components 'switch' and brightness,
meaning turing the light on or off will result in an update to brightness and vice versa.

````yaml
# Dimmable light controlled via MQTT
type: Lamp-dimmable
control: hue.set
switch:
  topic: test/lamp/switch
brightness:
  topic: test/brightness
````