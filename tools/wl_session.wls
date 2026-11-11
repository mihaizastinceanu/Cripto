#!/usr/bin/env wolframscript
(* Runs a .wl file block by block (blocks separated by blank lines) and prints a
   notebook-like transcript:  In[n]:= <code>   Out[n]= <result>
   usage: wolframscript -file wl_session.wls <input.wl> <transcript.txt> *)
{in, out} = $ScriptCommandLine[[2 ;; 3]];
SetDirectory[DirectoryName[ExpandFileName[in]]];
blocks = Select[StringTrim /@ StringSplit[Import[in, "Text"], RegularExpression["\\n\\s*\\n"]], # =!= "" &];
lines = {};
emit[s_] := (AppendTo[lines, s]; WriteString[$Output, s <> "\n"]);
Do[
  code = blocks[[i]];
  emit["In[" <> ToString[i] <> "]:= " <> StringReplace[code, "\n" -> "\n        "]];
  res = ToExpression[code];
  If[res =!= Null,
    emit["Out[" <> ToString[i] <> "]= " <> ToString[res, OutputForm, PageWidth -> Infinity]]];
  emit[""],
  {i, Length[blocks]}];
Export[out, StringRiffle[lines, "\n"], "Text", CharacterEncoding -> "UTF-8"];
