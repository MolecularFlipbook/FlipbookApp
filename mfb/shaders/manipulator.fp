uniform sampler2D texture;
uniform float opacity;

void main()
{
	vec4 color = texture2D(texture, gl_TexCoord[0].xy).rgba;
	gl_FragColor = vec4(color.r, color.g, color.b, color.a*opacity);
	gl_FragDepth = gl_FragCoord.z * 0.1;
}
