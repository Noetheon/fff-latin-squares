#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
using P = std::array<uint8_t,10>;

static P invp(const P& p){ P r{}; for(int i=0;i<10;i++) r[p[i]]=i; return r; }
static P comp(const P&a,const P&b){P r{};for(int i=0;i<10;i++)r[i]=a[b[i]];return r;}
static P rel(const P&a,const P&b){return comp(b,invp(a));}
static std::string ctype(const P&p){
  bool vis[10]={}; std::vector<int> v;
  for(int i=0;i<10;i++) if(!vis[i]){int x=i,n=0;do{vis[x]=1;x=p[x];n++;}while(x!=i);v.push_back(n);}
  std::sort(v.rbegin(),v.rend()); std::string s; for(size_t i=0;i<v.size();i++){if(i)s+='+';s+=std::to_string(v[i]);} return s;
}
static bool partial_has_odd(const std::array<int,10>&m){
  for(int s=0;s<10;s++) if(m[s]>=0){ int x=s; for(int len=1;len<=10;len++){ x=m[x]; if(x<0) break; if(x==s){ if(len>1 && (len&1)) return true; break; } } }
  return false;
}
static bool triple_cross_ok(const P&root,const P&q){
  const P id={0,1,2,3,4,5,6,7,8,9};
  std::array<P,3> rows{id,root,q};
  std::array<int,10> m;
  for(int c=0;c<10;c++)for(int d=c+1;d<10;d++){
    m.fill(-1); for(auto&r:rows)m[r[c]]=r[d]; if(partial_has_odd(m)) return false;
  }
  for(int u=0;u<10;u++)for(int v=u+1;v<10;v++){
    m.fill(-1); for(auto&r:rows){int cu=-1,cv=-1;for(int c=0;c<10;c++){if(r[c]==u)cu=c;if(r[c]==v)cv=c;}m[cu]=cv;} if(partial_has_odd(m)) return false;
  }
  return true;
}
static P root_from(const std::vector<int>& lens){P r{};int st=0;for(int L:lens){for(int j=0;j<L;j++)r[st+j]=st+(j+1)%L;st+=L;}return r;}
static uint64_t key(const P&p){uint64_t k=0;for(int i=0;i<10;i++)k|=(uint64_t)p[i]<<(4*i);return k;}
static P conjugate(const P&g,const P&q){return comp(comp(g,q),invp(g));}
static std::vector<P> residual_group(){
  std::vector<P> G; std::array<int,3> perm={0,1,2};
  do { for(int mask=0;mask<8;mask++){
    P g={0,1,2,3,4,5,6,7,8,9};
    for(int a=0;a<3;a++){
      int src0=4+2*a, src1=src0+1; int b=perm[a]; int dst0=4+2*b, dst1=dst0+1;
      if(mask&(1<<a)){g[src0]=dst1;g[src1]=dst0;}else{g[src0]=dst0;g[src1]=dst1;}
    }
    G.push_back(g);
  }} while(std::next_permutation(perm.begin(),perm.end()));
  return G;
}
static void run(const std::string&name,const P&root,const std::set<std::string>&allowed){
  P q={0,1,2,3,4,5,6,7,8,9}; uint64_t pre=0,stored=0; std::array<uint64_t,8>b{}; std::vector<P> tasks;
  do{
    if(!allowed.count(ctype(q))) continue;
    if(!allowed.count(ctype(rel(root,q)))) continue;
    pre++;
    if(!triple_cross_ok(root,q)) continue;
    if(q[0]<2||q[0]>9){throw std::runtime_error("bad bucket");}
    b[q[0]-2]++; stored++;
    if(q[0]==2) tasks.push_back(q);
  }while(std::next_permutation(q.begin(),q.end()));
  std::cout<<name<<" pre="<<pre<<" stored="<<stored<<" buckets=";for(auto x:b)std::cout<<x<<",";std::cout<<" tasks_q0_2="<<tasks.size()<<"\n";
  auto G=residual_group(); std::unordered_map<uint64_t,int> idx; idx.reserve(tasks.size()*2); for(int i=0;i<(int)tasks.size();i++)idx[key(tasks[i])]=i;
  std::vector<char> seen(tasks.size()); std::map<int,int> dist; int orbits=0; uint64_t cover=0;
  for(int i=0;i<(int)tasks.size();i++)if(!seen[i]){
    std::set<int> orb;
    for(auto&g:G){P z=conjugate(g,tasks[i]);auto it=idx.find(key(z));if(it==idx.end()){throw std::runtime_error("orbit image missing");}orb.insert(it->second);}
    for(int j:orb)seen[j]=1; dist[(int)orb.size()]++;orbits++;cover+=orb.size();
  }
  std::cout<<"group="<<G.size()<<" orbits="<<orbits<<" cover="<<cover<<" dist=";for(auto [s,n]:dist)std::cout<<n<<"*"<<s<<" ";std::cout<<"\n";
}
int main(){
  try {
  std::set<std::string> all={"10","8+2","6+4","6+2+2","4+4+2","4+2+2+2","2+2+2+2+2"};
  std::set<std::string> non=all;non.erase("2+2+2+2+2");
  run("noninv",root_from({4,2,2,2}),non);
  run("inv",root_from({2,2,2,2,2}),all);
  } catch(const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
