// Fresh exhaustive mod-2 4+4 occupied-cell exchange audit for supplied order-8 tables.
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
struct Item{unsigned __int128 profile;uint64_t cells;bool operator<(const Item&b)const{return profile<b.profile;}};
int insert(std::array<uint64_t,64>&b,uint64_t x){while(x){int i=63-__builtin_clzll(x);if(!b[i]){b[i]=x;return 1;}x^=b[i];}return 0;}
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("need input");std::ifstream f(argv[1]);if(!f)throw std::runtime_error("cannot open input");std::set<int> source_ids;int line;std::string s;std::map<int,int>lr,er,qr;int nt=0;uint64_t tested=0;
while(f>>line>>s){if(line<1||!source_ids.insert(line).second)throw std::runtime_error("duplicate or invalid source line");if(s.size()!=64)throw std::runtime_error("size");std::array<unsigned __int128,64>keys;std::array<uint64_t,64>lines{};int rankline=0;
for(int i=0;i<64;++i){int r=i/8,c=i%8,v=s[i]-'0';if(v<0||v>7)throw std::runtime_error("value");keys[i]=((unsigned __int128)1<<(3*r))+((unsigned __int128)1<<(3*(8+c)))+((unsigned __int128)1<<(3*(16+v)));rankline+=insert(lines,(1ull<<r)|(1ull<<(8+c))|(1ull<<(16+v)));}
for(int r=0;r<8;++r){unsigned a=0,b=0;for(int c=0;c<8;++c){a|=1u<<(s[r*8+c]-'0');b|=1u<<(s[c*8+r]-'0');}if(a!=255||b!=255)throw std::runtime_error("not Latin");}
std::vector<Item>sets;sets.reserve(635376);
for(int a=0;a<61;++a)for(int b=a+1;b<62;++b)for(int c=b+1;c<63;++c)for(int d=c+1;d<64;++d)sets.push_back({keys[a]+keys[b]+keys[c]+keys[d],(1ull<<a)|(1ull<<b)|(1ull<<c)|(1ull<<d)});
if(sets.size()!=635376)throw std::runtime_error("subset coverage");tested+=sets.size();std::sort(sets.begin(),sets.end());std::array<uint64_t,64>basis{};int rank=0;uint64_t pairs=0;
for(size_t a=0;a<sets.size();){size_t end=a+1;while(end<sets.size()&&sets[end].profile==sets[a].profile)++end;
for(size_t i=a;i<end;++i)for(size_t j=i+1;j<end;++j)if(!(sets[i].cells&sets[j].cells)){++pairs;rank+=insert(basis,sets[i].cells^sets[j].cells);}a=end;}
int q=64-rankline-rank;if(q<0)throw std::runtime_error("negative quotient");++nt;++lr[rankline];++er[rank];++qr[q];std::cout<<line<<","<<rankline<<","<<rank<<","<<q<<","<<pairs<<"\n";
}
if(!f.eof()||nt!=230)throw std::runtime_error("incomplete or malformed input");
std::cerr<<"tables="<<nt<<" four_subsets="<<tested<<"\nline ranks:";for(auto[a,b]:lr)std::cerr<<" "<<a<<":"<<b;std::cerr<<"\nexchange ranks:";for(auto[a,b]:er)std::cerr<<" "<<a<<":"<<b;std::cerr<<"\nquotient dims:";for(auto[a,b]:qr)std::cerr<<" "<<a<<":"<<b;std::cerr<<"\n";
}catch(std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
