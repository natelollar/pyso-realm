#version 450

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 colDiffuse;

out vec4 finalColor;

void main() {
        vec4 texelColor = texture(texture0, fragTexCoord);
        vec4 color = texelColor*colDiffuse*fragColor;
        // only way to get order independant blending ???
        // no blending for opacity gradient ???
        if (color.a <= 0){ 
                discard;
        }
        finalColor = color;
}