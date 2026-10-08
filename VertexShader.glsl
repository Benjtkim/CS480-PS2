#version 330 core
in vec3 aPos;
in vec3 aNormal;
in vec3 aColor;
in vec2 aTexture;

out vec3 vPos;
out vec3 vColor;
smooth out vec3 vNormal;
out vec2 vTexture;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
    vPos = vec3(model * vec4(aPos, 1.0));
    vColor = aColor;
    vNormal = normalize(transpose(inverse(model)) * vec4(aNormal, 0.0) ).xyz;
    vTexture = aTexture;
}
