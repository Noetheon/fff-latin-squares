if LoadPackage("primgrp") <> true then
  Error("PrimGrp did not load");
fi;
Print("GAP_VERSION=", GAPInfo.Version, "\n");
Print("PRIMGRP_VERSION=", PackageInfo("primgrp")[1].Version, "\n");
Print("DEGREE=10\n");
Print("COUNT=", NrPrimitiveGroups(10), "\n");
for i in [1..NrPrimitiveGroups(10)] do
  g := PrimitiveGroup(10, i);
  Print("GROUP\t", i, "\t", Size(g), "\t", StructureDescription(g), "\n");
od;
QUIT;
