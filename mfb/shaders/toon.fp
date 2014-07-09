uniform vec3 color;
uniform vec3 highlight;
//uniform float select;
uniform float time;
uniform float gray;

varying vec3 p;
varying vec3 n;
varying vec3 hv;

#define ambient 0.2
#define zOffset 1.0
#define SELECTRGB vec3(0.0,1.0,0.0)

void main()
{

	// calculate lighting
	vec3 normal = normalize(n);
	vec3 L = normalize(gl_LightSource[1].position.xyz - p);
	float diff = (gl_LightSource[1].diffuse * max(dot(normal,L), 0.0)).r;
	diff = pow(diff+0.9, 10.0);
	diff = clamp(diff, 0.0, 1.0);

	vec3 halfVec = normalize(hv);
	float nDotHV = max(dot(n, halfVec), 0.0);
	float spec = pow(nDotHV, 20.0);
	spec = pow(spec+0.9, 50.0);
	spec = clamp(spec, 0.0, 1.0);

	// calculate rim, and apply gamma correction
	float rim = 1.0-normal.z;

	// calculate surface color
	vec3 color = color*diff + color*ambient + spec * 0.1;
	float edge = pow(rim+0.4, 10.0);
	color = mix(color, vec3(0.0,0.0,0.0), edge);
	color = clamp(color, 0.0,1.0);

	// calculate gleam
	float gleam = sin((gl_FragCoord.x + gl_FragCoord.y+time*300.0)*0.02);
	gleam = (gleam * 0.5) + 0.7;

	// add hover highlight
	color +=  highlight * gleam;

	// add selection highlight
	/*if (select > 0.5 && false)
	{
		rim = pow(rim, 6.0);
		rim *= 10.0;
		if (rim<0.9)
		{
			rim = 0.0;
		}
		else
		{
			rim = 1.0;
		}

		color = mix(color, SELECTRGB,  rim);
	}*/

	if (gray > 0.5)
	{
		vec3 factor = vec3(0.3, 0.5, 0.2);
		float luma = dot(color, factor);
		color = mix(color, vec3(luma, luma, luma), 0.8);
		color = mix(color, vec3(1.0, 1.0, 1.0), 0.2);
	}

	vec4 finalColor = vec4(color.rgb, 1.0);
	gl_FragColor.rgba = finalColor;


}
