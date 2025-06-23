# Subsurf-Cleaner-Blender-Addon

![gifSubsurdCleanerNew](https://github.com/user-attachments/assets/29882a63-d945-4e9b-a6ac-66a1d7b9ce84)

Subsurf Cleaner:
A simple Blender addon that smooths your mesh using the Subdivision Surface modifier without adding new polygons.

How it works
The addon creates a temporary copy of the object.

Applies a Subdivision Surface modifier (level 1) to the copy.

Obtains the smoothed vertex coordinates.

Transfers these coordinates back to the original mesh.

What stays unchanged
Original mesh topology

UV maps

Materials

Vertex groups

Modifiers

Only the vertex positions are changed.

Modifier compatibility
Works with any modifiers, including Multiresolution.

Unlike previous versions, subdivision levels are no longer reset.

When changing the base mesh with Multiresolution, subdivision levels adjust to new coordinates — this is standard Blender behavior, not an addon issue.

Visual reference
The smoothing effect is similar to the “On Cage” mode in the Subdivision Surface modifier.

You get a smooth shape close to how the mesh looks with “On Cage” enabled.

Important note
The GIF above refers to the previous version.

In the new version, the Subdivision Surface modifier is not required on the original object.

Smoothing happens through a separate copy, isolating changes and preserving the original mesh structure.

🧠 Created with ChatGPT
Developed using artificial intelligence ChatGPT by OpenAI.

📜
Published under the Creative Commons Zero v1.0 Universal (CC0 1.0) license —
you are free to use, modify, and distribute the addon without attribution or restrictions, including for commercial purposes.
