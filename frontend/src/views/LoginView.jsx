import React, { useState } from "react";
import api from "../services/api";

export default function LoginView({ t, darkMode, setDarkMode, cardImg, onLogin }) {
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // login | register
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (authMode === "register") {
        await api.register(email, password, name);
      } else {
        await api.login(email, password);
      }
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{minHeight:"100vh",display:"flex",flexDirection:"column",justifyContent:"center",alignItems:"center",textAlign:"center",padding:"0",position:"relative",overflow:"hidden"}}>
      <button onClick={()=>setDarkMode(!darkMode)} style={{position:"absolute",top:20,left:20,zIndex:10,fontSize:16,background:"rgba(255,255,255,.12)",backdropFilter:"blur(8px)",border:"1px solid rgba(255,255,255,.2)",borderRadius:980,padding:"6px 12px",cursor:"pointer"}} onMouseEnter={e=>e.currentTarget.style.background="rgba(255,255,255,.25)"} onMouseLeave={e=>e.currentTarget.style.background="rgba(255,255,255,.12)"}>{darkMode?"\u2600\uFE0F":"\uD83C\uDF19"}</button>

      <div style={{position:"absolute",inset:0,zIndex:0,background:"linear-gradient(180deg, #0a1628 0%, #132d55 25%, #1a4a6e 45%, #2563a0 60%, #3b82f6 80%, #93c5fd 100%)"}}>
        <div style={{position:"absolute",inset:0,background:"radial-gradient(ellipse at 50% 70%, rgba(212,120,90,.15) 0%, transparent 60%)"}}/>
      </div>

      <div style={{position:"relative",zIndex:2,animation:"fu .8s ease",maxWidth:680,padding:"120px 24px 80px"}}>
        <p style={{fontSize:15,fontWeight:600,color:"rgba(255,255,255,.85)",letterSpacing:".08em",textTransform:"uppercase",marginBottom:16}}>ALL Accor+</p>
        <h1 style={{fontSize:"clamp(44px,8vw,80px)",fontWeight:700,lineHeight:1.05,letterSpacing:"-.04em",marginBottom:24,color:"white",textShadow:"0 2px 20px rgba(0,0,0,.3)"}}>{t.acad}</h1>
        <div style={{animation:"fu .8s ease .3s both",display:"flex",justifyContent:"center"}}>
          <img src={cardImg} alt="ALL Accor+ Explorer Card" style={{width:280,borderRadius:16,boxShadow:"0 20px 60px rgba(0,0,0,.35), 0 4px 16px rgba(0,0,0,.2)",transform:"perspective(800px) rotateY(-4deg) rotateX(2deg)",transition:"transform .4s ease"}} onMouseEnter={e=>e.target.style.transform="perspective(800px) rotateY(0deg) rotateX(0deg) scale(1.03)"} onMouseLeave={e=>e.target.style.transform="perspective(800px) rotateY(-4deg) rotateX(2deg)"}/>
        </div>

        {!showAuth ? (
          <div style={{animation:"fu .8s ease .6s both",display:"flex",gap:14,marginTop:32,justifyContent:"center",flexWrap:"wrap"}}>
            <button onClick={()=>onLogin("team_member")} style={{padding:"16px 34px",borderRadius:980,background:"rgba(255,255,255,.95)",border:"none",cursor:"pointer",boxShadow:"0 4px 24px rgba(0,0,0,.12)",transition:"all .2s",backdropFilter:"blur(12px)"}} onMouseEnter={e=>{e.currentTarget.style.transform="scale(1.05)";e.currentTarget.style.boxShadow="0 8px 32px rgba(0,0,0,.16)"}} onMouseLeave={e=>{e.currentTarget.style.transform="scale(1)";e.currentTarget.style.boxShadow="0 4px 24px rgba(0,0,0,.12)"}}><span className="apple-grad" style={{fontSize:17,fontWeight:700}}>{t.teamMember}</span></button>
            <button onClick={()=>onLogin("manager")} style={{padding:"16px 34px",borderRadius:980,background:"rgba(255,255,255,.95)",border:"none",cursor:"pointer",boxShadow:"0 4px 24px rgba(0,0,0,.12)",transition:"all .2s",backdropFilter:"blur(12px)"}} onMouseEnter={e=>{e.currentTarget.style.transform="scale(1.05)";e.currentTarget.style.boxShadow="0 8px 32px rgba(0,0,0,.16)"}} onMouseLeave={e=>{e.currentTarget.style.transform="scale(1)";e.currentTarget.style.boxShadow="0 4px 24px rgba(0,0,0,.12)"}}><span className="apple-grad" style={{fontSize:17,fontWeight:700}}>{t.manager}</span></button>
          </div>
        ) : (
          <div style={{animation:"fu .5s ease",marginTop:32,maxWidth:380,margin:"32px auto 0"}}>
            <form onSubmit={handleSubmit} style={{background:"rgba(255,255,255,.12)",backdropFilter:"blur(16px)",borderRadius:20,padding:"28px 24px",border:"1px solid rgba(255,255,255,.2)"}}>
              <h3 style={{fontSize:20,fontWeight:700,color:"white",marginBottom:16}}>{authMode === "login" ? "Sign In" : "Create Account"}</h3>
              {error && <p style={{color:"#ef4444",fontSize:13,marginBottom:12,background:"rgba(239,68,68,.15)",padding:"8px 12px",borderRadius:8}}>{error}</p>}
              {authMode === "register" && (
                <input type="text" placeholder="Full name" value={name} onChange={e=>setName(e.target.value)} required style={{width:"100%",padding:"12px 14px",borderRadius:10,border:"1px solid rgba(255,255,255,.3)",background:"rgba(255,255,255,.1)",color:"white",fontSize:15,marginBottom:10,boxSizing:"border-box"}}/>
              )}
              <input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} required style={{width:"100%",padding:"12px 14px",borderRadius:10,border:"1px solid rgba(255,255,255,.3)",background:"rgba(255,255,255,.1)",color:"white",fontSize:15,marginBottom:10,boxSizing:"border-box"}}/>
              <input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} required style={{width:"100%",padding:"12px 14px",borderRadius:10,border:"1px solid rgba(255,255,255,.3)",background:"rgba(255,255,255,.1)",color:"white",fontSize:15,marginBottom:16,boxSizing:"border-box"}}/>
              <button type="submit" disabled={loading} style={{width:"100%",padding:"14px",borderRadius:980,background:"white",border:"none",cursor:"pointer",fontSize:16,fontWeight:700,color:"#1d1d1f"}}>{loading ? "..." : (authMode === "login" ? "Sign In" : "Create Account")}</button>
              <p style={{fontSize:13,color:"rgba(255,255,255,.7)",marginTop:12,cursor:"pointer"}} onClick={()=>{setAuthMode(authMode==="login"?"register":"login");setError("");}}>
                {authMode === "login" ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </p>
            </form>
          </div>
        )}
      </div>
    </section>
  );
}
