// Cor do mar: verde-escuro no vale, mais claro na crista, ESPUMA branca nas cristas altas e íngremes.
VARYING float vAltura;
VARYING float vInclina;

void MAIN()
{
    vec3 fundo = vec3(0.006, 0.025, 0.02);
    vec3 crista = vec3(0.04, 0.13, 0.10);
    float t = smoothstep(-40.0 * agito, 45.0 * agito, vAltura);
    float espuma = smoothstep(0.55, 0.95, t) * smoothstep(0.12, 0.35, vInclina);
    vec3 cor = mix(fundo, crista, t);
    cor = mix(cor, vec3(0.62, 0.78, 0.70), espuma * 0.8);
    BASE_COLOR = vec4(cor, 1.0);
    ROUGHNESS = mix(0.18, 0.85, espuma);
    METALNESS = 0.0;
    SPECULAR_AMOUNT = 0.8;
}
