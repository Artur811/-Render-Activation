package com.ragestars.overlay;
import org.json.JSONObject;import java.io.*;import java.net.*;import java.nio.charset.StandardCharsets;
final class Api {
 static final String BASE_URL="https://ragestars-activation.onrender.com";
 static JSONObject post(String path,JSONObject body)throws Exception{URL url=new URL(BASE_URL+path);HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setRequestMethod("POST");c.setConnectTimeout(15000);c.setReadTimeout(15000);c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");try(OutputStream o=c.getOutputStream()){o.write(body.toString().getBytes(StandardCharsets.UTF_8));}int s=c.getResponseCode();InputStream in=s>=200&&s<300?c.getInputStream():c.getErrorStream();ByteArrayOutputStream b=new ByteArrayOutputStream();if(in!=null){byte[] a=new byte[4096];int n;while((n=in.read(a))!=-1)b.write(a,0,n);in.close();}c.disconnect();JSONObject r=new JSONObject(b.toString("UTF-8"));if(s<200||s>=300)throw new IOException(r.optString("error","HTTP "+s));return r;}
 static JSONObject activate(String code,String install)throws Exception{JSONObject b=new JSONObject();b.put("code",code.trim().toUpperCase());b.put("installation_id",install);return post("/activate",b);}
 static JSONObject check(String id,String token,String install)throws Exception{JSONObject b=new JSONObject();b.put("license_id",id);b.put("token",token);b.put("installation_id",install);return post("/check",b);}
}
