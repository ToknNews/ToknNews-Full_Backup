#!/bin/bash

# move into repo root
cd /var/www/toknnews-repo

echo "Creating ToknNews architecture..."

# config
mkdir -p config

# backend
mkdir -p backend/ingest \
         backend/compiler \
         backend/dashboard \
         backend/pm2 \
         backend/data/raw \
         backend/data/feeds \
         backend/data \
         backend/sandbox/devdata/raw \
         backend/sandbox/devdata/audio \
         backend/sandbox/devdata/audio_scripts

# audio
mkdir -p audio/dialogue \
         audio/music/beds \
         audio/music/stingers \
         audio/ambience \
         audio/sfx \
         audio/ads/sponsor_music_beds \
         audio/ads/sponsor_sfx \
         audio/ads/sponsor_voice \
         audio/scripts \
         audio/final

# dashboards
mkdir -p dashboards/system_dashboard \
         dashboards/ad_dashboard

# unreal
mkdir -p unreal/project/Config \
         unreal/project/Plugins \
         unreal/project/Content/ToknStudio/{Audio,Blueprints,Materials,Widgets,Metadata,Python,AdSlates} \
         unreal/python \
         unreal/docs

# blender + meshy
mkdir -p blender/src/props \
         blender/scripts \
         blender/exports \
         meshy/prompts \
         meshy/refs/concept_art

# pipeline
mkdir -p pipeline/from_chipstack \
         pipeline/queue \
         pipeline/outputs

# docs
mkdir -p docs

# README placeholders
find . -type d -not -path "./.git*" -exec sh -c 'echo "# $(basename "$1")" > "$1/README.md"' _ {} \;

echo "Architecture created."
echo "Add your docs into /docs then commit + push."
