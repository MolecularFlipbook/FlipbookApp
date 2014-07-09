uniform vec3 color;
uniform vec3 highlight;
//uniform float select;
uniform float time;
uniform float gray;

varying vec3 n;

#define ambient 0.2
#define zOffset 1.0
#define SELECTRGB vec3(0.0,1.0,0.0)

void main()
{

	// calculate lighting
	vec3 normal = normalize(n);
	
	// calculate rim, and apply gamma correction
	float rim = 1.0-normal.z;

	// calculate surface color
	// vec3 color = color*diff + color*ambient;
	vec3 color = color * rim * 2.0;
	// color = vec3(edge, edge, edge);
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
