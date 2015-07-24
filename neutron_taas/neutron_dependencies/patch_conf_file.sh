#!/bin/bash
#
# Copyright (C) 2015 Ericsson AB
# Copyright (C) 2015 Gigamon
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

INSERT_KEY="core_plugin"

T_CONF_FILE=$1
N_CONF_FILE=$2

if [ -z $T_CONF_FILE ] || [ -z $N_CONF_FILE ]; then
    echo "Usage: $0 <taas-conf-file> <neutron-conf-file>"
    exit 1
fi

ACTION="unspecified"

while read -r LINE; do
    # Skip blank lines
    if [ ${#LINE} -eq 0 ]; then
        continue;
    fi

    # Identify action to be performed based on section headers
    read -a WORD_ARRAY <<< $LINE
    if [[ ${WORD_ARRAY[0]} == "[DEFAULT]" ]]; then
        ACTION="merge"

        # Advance to next line
        continue
    fi
    if [[ ${WORD_ARRAY[0]} == "[taas]" ]]; then
        ACTION="append"

        # Add a blank line (separator) to Neutron config file
        echo "" >> $N_CONF_FILE
    fi

    # Execute action
    case $ACTION in
        "merge")
            KEY="${WORD_ARRAY[0]}"
            VALUE="${WORD_ARRAY[2]}"

            # Add 'value' to the end of the line beginning with 'key'
            # in the Neutron config file. If such a line does not 
            # exist, create a 'key = value' line and insert it just
            # after the line beginning with 'INSERT_KEY'.
            grep ^$KEY $N_CONF_FILE > /dev/null
            if [ $? -eq 0 ]; then
                sed -i "/^$KEY/ s/$/, $VALUE/" $N_CONF_FILE
            else
                sed -i "/^$INSERT_KEY/ a $KEY = $VALUE" $N_CONF_FILE
            fi
            ;;

        "append")
            # Add entire line to Neutron config file
            echo "$LINE" >> $N_CONF_FILE
            ;;

        *)
            ;;
    esac
done < $T_CONF_FILE

exit 0
