#!/bin/bash

read -p "Enter a name (use underscores for spaces): " custom_name
custom_name=${custom_name// /_}

yaml_content=$(cat <<EOF


views:
  - title: ALL PHASES ( 1+2+3)
    path: all-phases-1-2-3
    cards:
      - type: gauge
        entity: sensor.${custom_name}_multisensor_activepower_0
        min: -3000
        severity:
          green: -3000
          yellow: 0
          red: 0
        name: Active Power
        max: 3000
        needle: true
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_apparentpower_0
        detail: 1
        name: Apparent Power
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_current_0
        detail: 1
        name: Current
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_forwardactiveenergy_0
        detail: 1
        name: Forward Active Energy
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_frequency_0
        detail: 1
        name: Frequency
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reactivepower_0
        detail: 1
        name: Reactive Power
        unit: VAR
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reverseactiveenergy_0
        detail: 1
        name: Reverse Active Energy
    type: sidebar
  - title: Phase1
    path: active-power
    cards:
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_forwardactiveenergy_1
        detail: 1
        name: Forward Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reverseactiveenergy_1
        detail: 1
        name: Reverse Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_activepower_1
        detail: 1
        name: Active Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reactivepower_1
        detail: 1
        name: Reactive Power
        view_layout:
          position: main
        unit: VAR
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_apparentpower_1
        detail: 1
        name: Apparent Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_frequency_1
        detail: 1
        name: Frequency
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_voltage_1
        detail: 1
        name: Voltage
        view_layout:
          position: main
        icon: mdi:flash
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_current_1
        detail: 1
        name: Current
    type: sidebar
  - title: Phase2
    path: active-power2
    cards:
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_forwardactiveenergy_2
        detail: 1
        name: Forward Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reverseactiveenergy_2
        detail: 1
        name: Reverse Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_activepower_2
        detail: 1
        name: Active Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reactivepower_2
        detail: 1
        name: Reactive Power
        view_layout:
          position: main
        unit: VAR
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_apparentpower_2
        detail: 1
        name: Apparent Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_frequency_2
        detail: 1
        name: Frequency
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_voltage_2
        detail: 1
        name: Voltage
        view_layout:
          position: main
        icon: mdi:flash
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_current_2
        detail: 1
        name: Current
    type: sidebar
  - title: Phase3
    path: active-power3
    cards:
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_forwardactiveenergy_3
        detail: 1
        name: Forward Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reverseactiveenergy_3
        detail: 1
        name: Reverse Active Energy
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_activepower_3
        detail: 1
        name: Active Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_reactivepower_3
        detail: 1
        name: Reactive Power
        view_layout:
          position: main
        unit: VAR
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_apparentpower_3
        detail: 1
        name: Apparent Power
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_frequency_3
        detail: 1
        name: Frequency
        view_layout:
          position: main
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_voltage_3
        detail: 1
        name: Voltage
        view_layout:
          position: main
        icon: mdi:flash
      - graph: none
        type: sensor
        entity: sensor.${custom_name}_multisensor_current_3
        detail: 1
        name: Current
        view_layout:
          position: main
    type: sidebar
title: ${custom_name}
EOF
)

echo "$yaml_content" > "${custom_name}.yaml"

echo "YAML file '${custom_name}.yaml' generated successfully."
