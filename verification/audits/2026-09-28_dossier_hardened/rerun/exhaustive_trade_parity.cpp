// Independent C++ audit of three-view cycle-switch parity. No prior helper imported.
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <vector>
#include <set>
#include <map>
using Table=std::vector<std::vector<int>>;
std::vector<int> inv(const std::vector<int>& p){std::vector<int>q(p.size());for(int i=0;i<(int)p.size();++i)q[p[i]]=i;return q;}
int sign(const std::vector<int>& p){int q=1;for(int i=0;i<(int)p.size();++i)for(int j=i+1;j<(int)p.size();++j)if(p[i]>p[j])q=-q;return q;}
std::array<int,3> parity(const Table& l){int n=l.size();std::array<int,3>s{1,1,1};for(int a=0;a<n;++a){std::vector<int>col(n),sym(n);for(int r=0;r<n;++r)col[r]=l[r][a];for(int c=0;c<n;++c)for(int r=0;r<n;++r)if(l[r][c]==a)sym[c]=r;s[0]*=sign(l[a]);s[1]*=sign(col);s[2]*=sign(sym);}return s;}
Table view(const Table& l,int v){int n=l.size();Table t(n,std::vector<int>(n,-1));for(int r=0;r<n;++r)for(int c=0;c<n;++c){int s=l[r][c];if(v==0)t[r][c]=s;else if(v==1)t[c][r]=s;else t[s][c]=r;}return t;}
// Both coordinate exchanges are involutions, so the same function maps back.
void valid(const Table&l){int n=l.size();for(int v=0;v<2;++v)for(auto a:view(l,v)){std::sort(a.begin(),a.end());for(int x=0;x<n;++x)if(a[x]!=x)throw std::runtime_error("not Latin");}}
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("need tables file");std::ifstream f(argv[1]);if(!f)throw std::runtime_error("cannot open input");std::set<std::string> inputs;std::map<int,int> order_counts;int n;long long tables=0,trades=0,view_counts[3]={},expected[9]={};
while(f>>n){if(n!=2&&n!=4&&n!=6)throw std::runtime_error("unsupported order");Table l(n,std::vector<int>(n));for(auto&r:l)for(auto&x:r)if(!(f>>x))throw std::runtime_error("truncated input");valid(l);std::string key;for(int r=0;r<n;++r){if(l[0][r]!=r||l[r][0]!=r)throw std::runtime_error("not reduced");for(int c=0;c<n;++c)key+=char(48+l[r][c]);}if(!inputs.insert(key).second)throw std::runtime_error("duplicate square");++order_counts[n];auto before=parity(l);int global=((n*(n-1)/2)%2)?-1:1;if(before[0]*before[1]*before[2]!=global)throw std::runtime_error("RCS identity");++tables;
for(int v=0;v<3;++v){auto t=view(l,v);for(int a=0;a<n;++a)for(int b=a+1;b<n;++b){auto ib=inv(t[b]);std::vector<int>p(n),seen(n,0);for(int x=0;x<n;++x)p[x]=ib[t[a][x]];
std::vector<std::vector<int>> cycles;
for(int x=0;x<n;++x)if(!seen[x]){std::vector<int>cy;int y=x;do{seen[y]=1;cy.push_back(y);y=p[y];}while(y!=x);cycles.push_back(cy);}
for(unsigned mask=1;mask<(1u<<cycles.size());++mask){std::vector<int>support;for(unsigned k=0;k<cycles.size();++k)if(mask&(1u<<k))support.insert(support.end(),cycles[k].begin(),cycles[k].end());
auto changed=t;for(int c:support)std::swap(changed[a][c],changed[b][c]);auto z=view(changed,v);valid(z);auto after=parity(z);int delta=support.size()%2?-1:1;
for(int w=0;w<3;++w){int e=w==v?1:delta;if(after[w]!=before[w]*e)throw std::runtime_error("trade parity mismatch");}++trades;++view_counts[v];}}}}
if(!f.eof()||order_counts[2]!=1||order_counts[4]!=4||order_counts[6]!=9408)throw std::runtime_error("input census counts mismatch");
std::cout<<"{\"tables\":"<<tables<<",\"nonempty_cycle_union_trades\":"<<trades<<",\"by_view\":["<<view_counts[0]<<","<<view_counts[1]<<","<<view_counts[2]<<"],\"latin_failures\":0,\"parity_failures\":0,\"three_sign_identity_failures\":0}\n";
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
