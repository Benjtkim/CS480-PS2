#version 330 core

in vec3 vPos;
in vec3 vColor;
smooth in vec3 vNormal;
in vec2 vTexture;

uniform vec3 cColor;
uniform sampler2D textureImage;

out vec4 FragColor;
void main()
{
    // These three lines prevent GLSL from optimizing out attributes
    vec4 placeHolder = vec4(vPos+vColor+vNormal+vec3(vTexture, 1), 0);
    FragColor = -1 * abs(placeHolder);
    FragColor = clamp(FragColor, 0, 1);

    // Shade according to vertex colors
    FragColor = vec4(cColor, 1.0);
}
