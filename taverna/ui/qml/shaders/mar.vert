// Mar de tempestade (v0.56): soma de ondas que andam com o tempo; a normal sai da derivada (luz certinha).
VARYING float vAltura;
VARYING float vInclina;

void onda(vec2 p, vec2 dir, float comp, float vel, float amp, inout float h, inout vec2 d)
{
    float k = 6.2831 / comp;
    float f = dot(p, normalize(dir)) * k + tempo * vel;
    h += amp * sin(f);
    d += normalize(dir) * amp * k * cos(f);
}

void MAIN()
{
    vec4 w = MODEL_MATRIX * vec4(VERTEX, 1.0);
    vec2 p = w.xz;
    float h = 0.0;
    vec2 d = vec2(0.0);
    float forca = mix(1.0, 0.35, clamp(-p.y / 5000.0, 0.0, 1.0));     // lá longe as ondas parecem menores
    onda(p, vec2(1.0, 0.35), 900.0, 1.1, 38.0 * forca * agito, h, d);
    onda(p, vec2(0.6, 1.0), 520.0, 1.6, 22.0 * forca * agito, h, d);
    onda(p, vec2(-0.4, 1.0), 300.0, 2.3, 12.0 * forca * agito, h, d);
    onda(p, vec2(1.0, -0.2), 170.0, 3.1, 6.0 * forca * agito, h, d);
    onda(p, vec2(0.2, 1.0), 90.0, 4.4, 2.5 * forca * agito, h, d);
    VERTEX.y += h;
    NORMAL = normalize(vec3(-d.x, 1.0, -d.y));
    vAltura = h;
    vInclina = length(d);
}
