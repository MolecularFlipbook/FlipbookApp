uniform vec3 color;
uniform vec3 highlight;
//uniform float select;
uniform float time;
uniform float gray;

varying vec3 p;
varying vec3 n;

#define ambient 0.5
#define zOffset 1.0
#define SELECTRGB vec3(0.0,1.0,0.0)

//=============


void main()
{
	// vary normal
	vec3 normal = normalize(n);

	// calculate lighting
	vec3 L = normalize(gl_LightSource[1].position.xyz - p);
	float diff = max(dot(normal,L), 0.0);

	// calculate rim
	float rim = 1.0-normal.z;

	// calculate surface color
	vec3 color = diff*0.4 + color*ambient + rim*0.2;

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


	gl_FragColor.rgb = color;

	if (mod(gl_FragCoord.x, 2.0) <= 1.0 || mod(gl_FragCoord.y, 2.0) >= 1.0){
		discard;
		}

	if (highlight.r > 0.1){
		gl_FragDepth = gl_FragCoord.z * zOffset;
	}
	else{
		gl_FragDepth = gl_FragCoord.z;
	}


}
