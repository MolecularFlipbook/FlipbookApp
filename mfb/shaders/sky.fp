uniform vec4 color;
uniform float stretch;
uniform vec2 dimension;
uniform sampler2D texmap;

//varying vec3 p;
varying vec3 n;


void main()
{
	// vary normal
	vec3 normal = normalize(n);

	// load texture
	vec2 coord;
	if (stretch < 0.1){
		coord = gl_TexCoord[0].xy;
	}
	else
	{
		coord = vec2(gl_FragCoord.x / dimension.x, gl_FragCoord.y / dimension.y);
		//vec2 coordUV = gl_TexCoord[0].xy;
		//coord = mix(coord, coordUV, 0.1);
	}

	vec3 img = texture2D(texmap, coord).rgb;

	// calculate surface color
	vec3 color = mix(img, color.rgb, color.a);

	gl_FragColor.rgb = color;

}
