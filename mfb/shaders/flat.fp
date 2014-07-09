uniform vec3 color;
uniform vec3 highlight;
//uniform float select;
uniform float time;
uniform float gray;

//varying vec3 p;
varying vec3 n;

#define ambient 0.5
#define zOffset 1.0
#define SELECTRGB vec3(0.0,1.0,0.0)

//=============

vec3 mod289(vec3 x) {return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec2 mod289(vec2 x) {return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec3 permute(vec3 x) {return mod289(((x*34.0)+1.0)*x);}


//=============

void main()
{
	// vary normal
	vec3 normal = normalize(n);

	// calculate lighting


	// calculate rim
	float rim = 1.0 - normal.z;

	// calculate surface color
	vec3 color = color;

	// calculate gleam
	float gleam = sin((gl_FragCoord.x + gl_FragCoord.y+time*300.0)*0.02);
	gleam = (gleam * 0.5) + 0.7;

	// add hover highlight
	color +=  highlight * gleam;

	// add selection highlight
	/*
	if (select > 0.5 && false)
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

	if (highlight.r > 0.1){
		gl_FragDepth = gl_FragCoord.z * zOffset;
	}
	else{
		gl_FragDepth = gl_FragCoord.z;
	}


}
